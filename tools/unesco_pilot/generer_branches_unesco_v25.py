#!/usr/bin/env python3
"""Partitionner un export JSON officiel UNESCO en manifestes MT pour catalogue v25.

Attend un objet JSON {'concepts':[...]} avec microthesaurus_ids par concept.
N'invente ni microthesaurus absents ni correspondances wikidata / Wikipedia.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import shutil


def safe(s):
    return bool(re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]{0,90}', s))


def run(source: Path, dest: Path, revision: str, prefix='unesco.full'):
    if not source.is_file():
        raise ValueError('JSON UNESCO absent: ' + str(source))
    if not safe(revision) or not safe(prefix):
        raise ValueError('Version ou prefixe invalide')
    if dest.exists():
        raise ValueError('Destination deja presente, refuser remplacement: ' + str(dest))
    raw = source.read_bytes()
    data = json.loads(raw.decode('utf-8-sig'))
    concepts = data.get('concepts')
    if not isinstance(concepts, list) or not concepts:
        raise ValueError('Objet JSON attendu avec tableau concepts non vide')
    groups = defaultdict(list)
    missing = 0
    ids = set()
    for c in concepts:
        cid = c.get('unesco_id')
        if not isinstance(cid, str) or not safe(cid) or cid in ids:
            raise ValueError('Concept duplique ou sans identite stable')
        ids.add(cid)
        mids = c.get('microthesaurus_ids', [])
        if not isinstance(mids, list) or not mids:
            missing += 1
            continue
        for mid in sorted(set(mids)):
            if not isinstance(mid, str) or not re.fullmatch(r'mt\d+\.\d+', mid):
                raise ValueError('Microthesaurus inconnu: ' + str(mid))
            groups[mid].append(c)
    if not groups:
        raise ValueError('Aucun concept avec microthesaurus_ids reconnu')
    dest.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='.v25_branches_', dir=dest.parent))
    try:
        manifests = []
        for mid in sorted(groups, key=lambda x: tuple(map(int,x[2:].split('.')))):
            base = mid.replace('.', '_')
            concept_file = 'concepts_' + base + '.json'
            bridges = 'ponts_' + base + '.csv'
            branch_file = 'branche_' + base + '.json'
            (work / concept_file).write_text(json.dumps({'concepts': sorted(groups[mid], key=lambda c: c['unesco_id'])},
                                                         ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
            (work / bridges).write_text('concept_id,category_title,status,justification,depth_limit\n', encoding='utf-8')
            manifest = {'schema': 'encyklopedia.branch-manifest.v25/1',
                        'branch_id': prefix + '.' + mid, 'branch_version': revision,
                        'vocabulary': 'unesco', 'title_fr': 'UNESCO ' + mid,
                        'concepts_file': concept_file, 'bridges_file': bridges,
                        'discovery': {'auto_exact_category_roots': True, 'auto_root_depth': 0,
                                      'max_reviewed_root_depth': 2, 'max_category_tasks': 15000,
                                      'max_members_per_category': 50000},
                        'origin': {'input_sha256': hashlib.sha256(raw).hexdigest(),
                                   'nature': 'UNESCO_SOURCE_PRESERVEE_NON_CANONIQUE'}}
            (work / branch_file).write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
            manifests.append({'branch_id': manifest['branch_id'], 'manifest': branch_file,
                              'concept_count': len(groups[mid])})
        index = {'schema': 'encyklopedia.generated-branches-v25/1',
                 'source_sha256': hashlib.sha256(raw).hexdigest(),
                 'source_concepts': len(concepts), 'concepts_without_microthesaurus': missing,
                 'branches': manifests, 'claim': 'PARTITION_OF_PROVIDED_FILE_ONLY_NOT_ALL_UNESCO'}
        (work / 'BRANCHES_INDEX_V25.json').write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        work.rename(dest)
        return index
    finally:
        if work.exists():
            shutil.rmtree(work)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--dest', type=Path, required=True)
    p.add_argument('--revision', required=True)
    p.add_argument('--prefix', default='unesco.full')
    a = p.parse_args()
    try:
        print(json.dumps(run(a.source, a.dest, a.revision, a.prefix), ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as e:
        print(json.dumps({'status': 'V25_GENERATOR_REFUS', 'reason': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(2)
