"""UNESCO Educational Policy, étape 6 : graphe de revue privé, non canonique.

Une seule branche, 41 concepts, 85 propositions IA déjà réceptionnées,
234 observations SKOS. N'écrit jamais de KQ/KP/KA/KS canoniques et ne publie rien.
N'utilise ni réseau ni SQLite ni le gros XML Wikipédia.

Python >= 3.10, bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

BRANCH = 'unesco-mt1-10'
STAGE4 = 'koa.unesco-mt1-10-semantic-stage/1.0'
STAGE5 = 'kristalizer.unesco-mt1-10-ai-claim-candidates/1.0'
EXPECTED_STAGE5_SHA_NORMALIZED = '595adbf3d6cc7c9d0d47ba8ec495666197012f19b68ce0a949f4f97970cdc0e7'
EXPECTED_DOSSIER_SHA = 'c4b5f2ce5c837ab00a4cda1de8f6dc980a2eb315ab1a9f665ff63b378e281d60'
STAGE6 = 'koa.unesco-mt1-10-precanonical-branch-graph/1.0'
DEFAULT_WORK = Path(r'D:\EncyKlopedia\30_working\unesco_mt1_10\autopilot_concept10_puis_41')
LOCALES = ('en', 'fr', 'es', 'de', 'nl', 'sv', 'da', 'no', 'nn', 'fi', 'et', 'af', 'it', 'pt')

class Stage6Error(ValueError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_from(path: Path, limit: int = 8_000_000):
    if not path.is_file() or not (0 < path.stat().st_size <= limit):
        raise Stage6Error(f'JSON absent ou trop volumineux : {path}')
    try:
        return json.loads(path.read_bytes().decode('utf-8-sig'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Stage6Error(f'JSON invalide : {path}: {exc}') from exc


def encode_json(obj) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')


def encode_csv(fields, rows):
    buf = io.StringIO(newline='')
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction='ignore', lineterminator='\r\n')
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode('utf-8-sig')


def safe_work(work: Path, out: Path):
    work = work.resolve()
    out = out.resolve()
    if out == work or out in (work / 'semantic_stage_v4', work / 'semantic_stage_v5'):
        raise Stage6Error('Destination interdite : ne pas écraser les entrées')
    if out != work / 'semantic_stage_v6' and out.parent != work:
        raise Stage6Error('Sortie obligatoire dans le dossier de recherche privé')
    for candidate in (out, *out.parents):
        if (candidate / '.git').exists():
            raise Stage6Error(f'Dossier Git interdit pour des données de recherche : {candidate}')
    if out.is_symlink():
        raise Stage6Error('Lien symbolique interdit pour la sortie')
    return work, out


def load_sources(work: Path):
    v4 = work / 'semantic_stage_v4'
    v5 = work / 'semantic_stage_v5' / 'candidats_chatgpt_reception_kristalizer.json'
    mpath = v4 / 'manifest.json'
    m = json_from(mpath)
    if (m.get('format') != STAGE4 or m.get('branch') != BRANCH or
        m.get('one_branch_kristal') is not True or m.get('public_release_authorized') is not False or
        m.get('canonical_assertions_approved') != 0 or m.get('canonical_kristal_built') is not False or
        m.get('concept_count') != 41 or m.get('candidate_qids') != 36 or
        m.get('skos_observed_edge_count') != 234 or m.get('cross_branch_link_count') != 112 or
        m.get('languages_planned') != list(LOCALES) or m.get('projection_slots') != 574):
        raise Stage6Error('Manifeste étape 4 incompatible ou preuve de canonisation non attendue')
    source_names = {
        'dossier': work / 'skope_dossier.json',
        'inventory': work / 'inventory.json',
        'queue': work / 'projection_queue_14_langues.json',
        'report': work / 'RAPPORT_AUTO.json',
        'xml_manifest': work / 'wikipedia_extract' / 'manifest.json',
    }
    hashes = {}
    for label, path in source_names.items():
        if not path.is_file() or path.stat().st_size > 10_000_000:
            raise Stage6Error(f'Source absente ou non bornée : {path}')
        current = sha(path.read_bytes())
        if current != m.get('source_sha256', {}).get(label):
            raise Stage6Error(f'Empreinte source étape 4 incohérente : {label}')
        hashes[label] = current
    if hashes['dossier'] != EXPECTED_DOSSIER_SHA:
        raise Stage6Error('Ce lot IA n’appartient pas à ce dossier Skope précis')
    if not v5.is_file() or v5.stat().st_size > 3_000_000:
        raise Stage6Error(f'Réception Kristalizer étape 5 absente : {v5}')
    vb = v5.read_bytes()
    try:
        norm = vb.decode('utf-8').replace('\r\n', '\n').encode('utf-8')
    except UnicodeDecodeError as exc:
        raise Stage6Error('La réception Kristalizer n’est pas en UTF-8 valide') from exc
    if sha(norm) != EXPECTED_STAGE5_SHA_NORMALIZED:
        raise Stage6Error('Réception Kristalizer modifiée ou non conforme au lot 85 validé')
    p = json_from(v5)
    if (p.get('profile') != STAGE5 or p.get('branch') != BRANCH or
        p.get('one_branch_kristal') is not True or p.get('not_canonical') is not True or
        p.get('publication_authorized') is not False or p.get('unreviewed_ai_proposals') is not True or
        p.get('canonical_assertions_minted') != 0 or p.get('source_dossier_sha256') != hashes['dossier'] or
        p.get('proposed_count') != 85):
        raise Stage6Error('Contrat étape 5 incorrect')
    props = p.get('proposals')
    if not isinstance(props, list) or len(props) != 85:
        raise Stage6Error('Les 85 propositions attendues ne sont pas présentes')
    if m.get('missing_candidate_qids') != ['concept5999', 'concept6020', 'concept17112', 'concept17163', 'concept17189']:
        raise Stage6Error('Liste des concepts sans QID inattendue')
    return m, props, hashes, sha(norm)


def build(work: Path):
    manifest, proposals, source_shas, v5_sha = load_sources(work)
    cards_dir = work / 'semantic_stage_v4' / 'cards'
    card_paths = sorted(cards_dir.glob('concept*.json'))
    if len(card_paths) != 41:
        raise Stage6Error(f'41 fiches attendues; trouvées : {len(card_paths)}')
    cards = {}
    card_hashes = {}
    for path in card_paths:
        c = json_from(path, 100_000)
        cid = c.get('unesco_id')
        if (not isinstance(cid, str) or not re.fullmatch(r'concept\d+', cid) or
            path.stem != cid or cid in cards or c.get('branch') != BRANCH or
            c.get('one_branch_kristal') is not True or c.get('public_release_authorized') is not False or
            c.get('canonical_KQ') is not None or c.get('canonical_KA') != [] or
            c.get('canonical_KP') != [] or c.get('canonical_KS') != []):
            raise Stage6Error(f'Fiche dangereuse ou non canonique : {path}')
        qid = c.get('wikidata_qid_candidate')
        if qid is not None and (not isinstance(qid, str) or not re.fullmatch(r'Q[1-9]\d*', qid)):
            raise Stage6Error(f'QID candidat invalide : {cid}')
        if c.get('wikidata_mapping_status') != 'UNREVIEWED_EXTERNAL_CANDIDATE':
            raise Stage6Error(f'Correspondance QID déjà approuvée ou statut inattendu : {cid}')
        if c.get('unesco_uri') != 'http://vocabularies.unesco.org/thesaurus/' + cid:
            raise Stage6Error(f'URI UNESCO inattendue : {cid}')
        if c.get('target_locales') != list(LOCALES):
            raise Stage6Error(f'Langues inattendues : {cid}')
        cards[cid] = c
        card_hashes[cid] = sha(path.read_bytes())
    if sum(c['wikidata_qid_candidate'] is not None for c in cards.values()) != 36:
        raise Stage6Error('Nombre de QID incohérent')
    ordered = sorted(cards, key=lambda v: (v != 'concept10', int(v.removeprefix('concept'))))
    skos = json_from(work / 'semantic_stage_v4' / 'skos_candidate_edges.json')
    edges = skos.get('edges')
    if not isinstance(edges, list) or len(edges) != 234:
        raise Stage6Error('234 relations SKOS requises')
    seen_edges = set()
    for edge in edges:
        if not isinstance(edge, dict):
            raise Stage6Error('Arête SKOS invalide')
        src, dst = edge.get('from_unesco_id'), edge.get('to_unesco_id')
        k = (src, edge.get('relation'), dst)
        if (src not in cards or not isinstance(dst, str) or not re.fullmatch(r'concept\d+', dst) or
            edge.get('relation') not in ('broader', 'narrower', 'related') or
            edge.get('authority') != 'UNESCO_SKOS_OBSERVED_NOT_KA' or
            edge.get('to_branch_member') is not (dst in cards) or k in seen_edges):
            raise Stage6Error(f'Relation SKOS non admissible : {k}')
        seen_edges.add(k)
    outside = sum(e['to_branch_member'] is False for e in edges)
    if outside != 112:
        raise Stage6Error('Nombre de liens transversaux modifié')
    claims = []
    counts = {cid: 0 for cid in cards}
    refs_seen = set()
    context_count = 0
    matched_page_ids = set()
    for p in proposals:
        cid, rid = p.get('unesco_id'), p.get('proposal_ref')
        if cid not in cards or not isinstance(rid, str) or rid in refs_seen:
            raise Stage6Error('Proposition hors branche ou identifiant dupliqué')
        refs_seen.add(rid)
        if (p.get('canonical_KA') is not None or p.get('canonical_KS') != [] or
            p.get('epistemic_status') != 'AI_CANDIDATE_NOT_ASSERTION' or
            p.get('review_status') != 'PENDING' or p.get('source_validation') != 'PENDING' or
            p.get('copyright_review') != 'PENDING'):
            raise Stage6Error(f'Proposition déjà transformée ou non conforme : {rid}')
        text = p.get('text_candidate')
        if not isinstance(text, str) or not text.strip():
            raise Stage6Error(f'Texte absent : {rid}')
        sources = p.get('research_context_refs')
        if not isinstance(sources, list) or p.get('local_research_context_count') != len(sources):
            raise Stage6Error(f'Contextes incohérents : {rid}')
        for s in sources:
            if s.get('source_type') == 'wikipedia_en':
                matches = [w for w in cards[cid]['wikipedia_en'] if w.get('page_id') == s.get('page_id')]
                if (len(matches) != 1 or matches[0].get('is_redirect') is not False or
                    matches[0].get('candidate_context_usable') is not True or
                    str(matches[0].get('revision_id')) != str(s.get('revision_id')) or
                    matches[0].get('sha256') != s.get('sha256') or
                    s.get('verified_as') != 'LOCAL_TEXT_IDENTITY_ONLY'):
                    raise Stage6Error(f'Contexte Wikipédia non admissible : {rid}')
                matched_page_ids.add(s['page_id'])
            elif s.get('source_type') == 'unesco':
                if s.get('uri') != cards[cid]['unesco_uri'] or s.get('verified_as') != 'LOCAL_POINTER_ONLY':
                    raise Stage6Error(f'Pointeur UNESCO non conforme : {rid}')
            else:
                raise Stage6Error(f'Contexte non reconnu : {rid}')
        counts[cid] += 1
        context_count += len(sources)
        claims.append({
            'proposal_ref': rid,
            'subject_review_ref': 'candidate:unesco:' + cid,
            'unesco_id': cid,
            'text_candidate': text,
            'research_context_refs': sources,
            'model_id': p['model_id'],
            'generation_ref': p['generation_ref'],
            'epistemic_status': 'UNREVIEWED_AI_PROPOSAL',
            'factual_review_status': 'PENDING',
            'identity_review_status': 'PENDING',
            'source_review_status': 'PENDING',
            'not_a_KA': True,
        })
    if set(counts) != set(cards) or min(counts.values()) == 0 or len(claims) != 85 or context_count != 16:
        raise Stage6Error('Couverture IA ou nombre de contextes non conforme')
    # Aucun re-scan XML: contrôles de petits fichiers extraits localement uniquement.
    for pid in matched_page_ids:
        page_file = work / 'wikipedia_extract' / f'page-{pid}.wikitext.txt'
        if not page_file.is_file() or page_file.stat().st_size > 8_000_000:
            raise Stage6Error(f'Texte Wikipédia local absent : {page_file}')
        relevant = [r for p in proposals for r in p['research_context_refs']
                    if r.get('source_type') == 'wikipedia_en' and r.get('page_id') == pid]
        if any(sha(page_file.read_bytes()) != r['sha256'] for r in relevant):
            raise Stage6Error(f'Texte Wikipédia local modifié : {pid}')
    lexical = {}
    nodes = []
    for cid in ordered:
        c = cards[cid]
        lexical[cid] = c['labels']
        nodes.append({
            'review_ref': 'candidate:unesco:' + cid,
            'unesco_id': cid,
            'unesco_uri': c['unesco_uri'],
            'lexical_ref': f'lexique_observe.json#/labels/{cid}',
            'external_qid_candidate': c['wikidata_qid_candidate'],
            'wikidata_crosswalk_status': 'PENDING_NO_EXACT_MATCH',
            'canonical_KQ': None,
            'review_card_sha256': card_hashes[cid],
            'candidate_proposals': counts[cid],
            'skos_relation_count': sum(e['from_unesco_id'] == cid for e in edges),
            'wikipedia_research_context_count': sum(w.get('candidate_context_usable') is True and not w.get('is_redirect', True) for w in c.get('wikipedia_en', [])),
        })
    graph = {
        'format': STAGE6,
        'branch': BRANCH,
        'one_branch_kristal': True,
        'stage': 'PRECANONICAL_REVIEW_GRAPH_ONLY',
        'framework_v11_canonical_graph': False,
        'eligible_for_kit_enable_v11': False,
        'public_release_authorized': False,
        'canonical_KQ_KP_KA_KS_created': 0,
        'wikidata_exact_matches_approved': 0,
        'semantic_nodes': nodes,
        'skos_observations_not_KA': edges,
        'unreviewed_ai_proposals_not_KA': claims,
        'external_references_not_branch_members': sorted(set(e['to_unesco_id'] for e in edges if e['to_branch_member'] is False)),
        'provenance_sha256': {'skope_dossier': source_shas['dossier'],
                              'kristalizer_received_json_lf_normalized': v5_sha,
                              'stage4_manifest': sha((work / 'semantic_stage_v4' / 'manifest.json').read_bytes()),
                              'stage4_edges': sha((work / 'semantic_stage_v4' / 'skos_candidate_edges.json').read_bytes())},
    }
    report = {
        'format': 'koa.unesco-mt1-10-precanonical-stage-report/1.0',
        'branch': BRANCH,
        'status': 'PRIVATE_PRECANONICAL_GRAPH_PREPARED',
        'concepts': len(nodes), 'candidate_qids': 36, 'missing_candidate_qids': manifest['missing_candidate_qids'],
        'skos_observations': len(edges), 'internal_skos_observations': len(edges) - outside,
        'cross_branch_skos_observations': outside,
        'ai_proposals': len(claims), 'ai_proposals_with_local_context_refs': sum(bool(c['research_context_refs']) for c in claims),
        'local_context_refs': context_count,
        'local_wikipedia_page_ids_rechecked': len(matched_page_ids),
        'concept10_ai_proposals': counts['concept10'],
        'target_locales': list(LOCALES), 'projections_planned': len(nodes)*len(LOCALES),
        'generated_articles': 0, 'new_ai_model_calls': 0,
        'canonical_kristal_built': False, 'canonical_KQ_KP_KA_KS_created': 0,
        'qualified_runtime_sets': False, 'public_release_authorized': False,
        'next': 'Decisions sur identites, preuves et assertions; creation via Kit dans workspace explicite; validation v11 distincte',
    }
    reviews_concepts = []
    for cid in ordered:
        c = cards[cid]
        reviews_concepts.append({
            'unesco_id':cid,'label_en':' | '.join(c['labels'].get('en',[])),
            'wikidata_qid_candidate':c['wikidata_qid_candidate'] or '',
            'identity_decision':'PENDING','proposed_KQ':'','approved_KQ':'',
            'reviewer':'','review_ref':'','notes':'',
        })
    reviews_proposals = []
    for p in claims:
        reviews_proposals.append({
            'proposal_ref':p['proposal_ref'],'unesco_id':p['unesco_id'],
            'statement_text':p['text_candidate'],'context_refs':len(p['research_context_refs']),
            'factual_decision':'PENDING','property_mapping':'',
            'canonical_KA':'','approved_KS':'','reviewer':'','review_ref':'','notes':''
        })
    reviews_relations = []
    for i, e in enumerate(edges, 1):
        reviews_relations.append({'observation_num':i,'source_id':e['from_unesco_id'],
                                  'relation':e['relation'],'target_id':e['to_unesco_id'],
                                  'target_in_branch':str(e['to_branch_member']).lower(),
                                  'semantic_promotion_decision':'PENDING','reviewer':'','review_ref':'','notes':''})
    lexique = {'format':'koa.unesco-mt1-10-observed-labels/1.0', 'branch':BRANCH,
               'source':'UNESCO_LOCAL_SKOS_OBSERVATIONS_NOT_LANGUAGE_REALIZATIONS',
               'direct_qualified_locale_coverage':0,'labels':lexical,'publication_authorized':False}
    intro = ('# UNESCO Educational Policy — étape 6 : revue de concept10\n\n'
             '**Ce fichier est un brouillon de revue, non un Kristal canonique.**\n\n'
             f"- Concept : `{nodes[0]['unesco_id']}` — {lexical['concept10'].get('en', [''])[0]}\n"
             f"- QID Wikidata proposé (non approuvé) : `{cards['concept10']['wikidata_qid_candidate']}`\n"
             f"- Liens SKOS observés : {nodes[0]['skos_relation_count']}\n"
             f"- Propositions IA : {counts['concept10']}\n\n"
             '## Questions avant toute canonisation\n\n'
             '1. Quel KQ validé et quel référent sémantique identifient ce concept ?\n'
             '2. Quelles propositions sont factuellement admissibles, et avec quel contexte juridictionnel ?\n'
             '3. Quels KS vérifiables apportent réellement la preuve ? Le texte Wikipédia est un contexte, non un KS approuvé.\n'
             '4. Quels KP expriment les relations attestées sans convertir automatiquement SKOS en KA ?\n\n'
             '## Propositions à examiner\n\n')
    for item in claims:
        if item['unesco_id'] == 'concept10':
            intro += f"### {item['proposal_ref']}\n\n{item['text_candidate']}\n\nÉtat : PENDING — source indépendante à vérifier.\n\n"
    intro += ('## Statut de sortie\n\nAucun KQ, KP, KA ou KS n’a été créé; aucun article ni état public n’a été publié.\n')
    files = {
        'graphe_candidat_prive.json': encode_json(graph),
        'lexique_observe.json': encode_json(lexique),
        'REVUE_41_CONCEPTS.csv': encode_csv(list(reviews_concepts[0]), reviews_concepts),
        'REVUE_85_PROPOSITIONS.csv': encode_csv(list(reviews_proposals[0]), reviews_proposals),
        'REVUE_234_RELATIONS_SKOS.csv': encode_csv(list(reviews_relations[0]), reviews_relations),
        'REVUE_CONCEPT10.md': intro.encode('utf-8'),
        'RAPPORT_ETAPE6.json': encode_json(report),
    }
    digest = {'format':'koa.unesco-mt1-10-stage6-files/1.0','branch':BRANCH,
              'files_sha256': {name:sha(content) for name,content in sorted(files.items())},
              'upstream_sha256': {'v5_normalized':v5_sha,'dossier':source_shas['dossier']},
              'publication_authorized':False}
    files['MANIFESTE_FICHIERS_SHA256.json'] = encode_json(digest)
    return files, report


def install(files, out: Path):
    if out.exists():
        if not out.is_dir() or any(p.is_symlink() for p in out.iterdir()):
            raise Stage6Error('Dossier de sortie non standard')
        actual = {p.name for p in out.iterdir() if p.is_file()}
        if actual != set(files):
            raise Stage6Error('Sortie existante différente; ne rien écraser, choisir une nouvelle sauvegarde')
        for name, content in files.items():
            if sha((out / name).read_bytes()) != sha(content):
                raise Stage6Error(f'Sortie existante modifiée, aucun écrasement : {name}')
        return 'DEJA_PRESENT_IDENTIQUE'
    out.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='.stage6-en-construction-', dir=out.parent))
    try:
        for name, content in files.items():
            (temp / name).write_bytes(content)
        # N'utilise pas shutil.move : opération atomique de renommage si possible.
        if out.exists():
            raise Stage6Error('Une sortie est apparue pendant la préparation')
        temp.rename(out)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return 'NOUVEAU_DOSSIER'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--work', type=Path, default=DEFAULT_WORK, help='Dossier de recherche créé par l’autopilote')
    ap.add_argument('--check-only', action='store_true', help='Valide les entrées sans écrire la sortie')
    ns = ap.parse_args(argv)
    try:
        work, out = safe_work(ns.work, ns.work / 'semantic_stage_v6')
        files, report = build(work)
        result = 'VERIFICATION_SEULE' if ns.check_only else install(files, out)
        print(json.dumps({'stage':6,'result':result,'out':str(out),**report}, ensure_ascii=False, indent=2))
        return 0
    except (Stage6Error, OSError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({'status':'BLOCKED_NO_CANONICAL_WRITES','error':str(exc),
                          'public_release_authorized':False}, ensure_ascii=False),file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
