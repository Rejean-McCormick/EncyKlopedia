#!/usr/bin/env python3
"""Read-only candidate lexical quality audit for EncyKlopedia index v1.

Reads existing lexical.sqlite3 and small UniMorph source ZIPs; never modifies them.
Derived audit/checkpoints/CSV/reports are written only under quality-v1 on data D:.
No canonical diK matches, no semantic equivalence, no publication.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import json
import os
import re
import shutil
import sqlite3
import sys
import zipfile
from collections import Counter
from contextlib import closing
from pathlib import Path

from lexical_indexer import SUBDIR, atomic_csv, atomic_json, exclusive_lock, parse_morph, unimorph_members, utc, valid_lake

QUALITY_SUBDIR = Path('30_working/lexical/harvester/quality-v1')
QUALITY_SCHEMA = '''
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS language_audit (
 language_code TEXT PRIMARY KEY,
 observation_rows INTEGER NOT NULL,
 distinct_lemma_keys INTEGER NOT NULL,
 repeated_lemma_keys INTEGER NOT NULL,
 extra_observation_rows INTEGER NOT NULL,
 repeated_inside_one_source_keys INTEGER NOT NULL,
 shared_across_files_keys INTEGER NOT NULL,
 shared_across_families_keys INTEGER NOT NULL,
 kaikki_unimorph_keys INTEGER NOT NULL,
 kaikki_wikidata_keys INTEGER NOT NULL,
 unimorph_wikidata_keys INTEGER NOT NULL,
 completed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS overlap_examples (
 language_code TEXT NOT NULL,
 lemma_key TEXT NOT NULL,
 observation_rows INTEGER NOT NULL,
 source_file_count INTEGER NOT NULL,
 family_count INTEGER NOT NULL,
 family_labels TEXT NOT NULL,
 source_ids TEXT NOT NULL,
 PRIMARY KEY(language_code,lemma_key)
);
'''
FAMILIES = {'kaikki': 1, 'unimorph': 2, 'wikidata': 4}
FOCUS = ('pib', 'sdh')


def readonly_connection(path: Path):
    if not path.is_file():
        raise FileNotFoundError(f'Index SQLite introuvable: {path}')
    conn = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=30)
    conn.execute('PRAGMA query_only=ON')
    conn.execute('PRAGMA busy_timeout=30000')
    mandatory = {'entries', 'source_files', 'language_stats'}
    schema = {row[0] for row in conn.execute('SELECT name FROM sqlite_master WHERE type="table"')}
    if not mandatory <= schema:
        conn.close()
        raise ValueError('Le fichier SQLite ne correspond pas au schéma lexical attendu.')
    return conn


def db_fingerprint(conn):
    """Fast invariant over catalog contents; detects changes without scanning entries."""
    h = hashlib.sha256()
    ver = conn.execute('PRAGMA user_version').fetchone()[0]
    h.update(f'lexical-quality-v1|{ver}\n'.encode())
    for row in conn.execute('''SELECT id,relative_path,kind,edition,size_bytes,mtime_ns,
            status,cursor_lines,accepted,rejected FROM source_files ORDER BY id'''):
        h.update(json.dumps(row, ensure_ascii=False, separators=(',', ':')).encode('utf-8') + b'\n')
    for row in conn.execute('''SELECT source_id,language_code,lemma_observations,
            sense_observations,form_observations,translation_observations
            FROM language_stats ORDER BY source_id,language_code'''):
        h.update(json.dumps(row, ensure_ascii=False, separators=(',', ':')).encode('utf-8') + b'\n')
    return h.hexdigest()


def candidates(conn):
    return list(conn.execute('''SELECT language_code, SUM(lemma_observations)
        FROM language_stats GROUP BY language_code ORDER BY language_code'''))


def source_families(conn):
    result = {}
    for sid, kind in conn.execute('SELECT id,kind FROM source_files'):
        if kind not in FAMILIES:
            raise ValueError(f'Source kind inattendu: {kind}')
        result[sid] = FAMILIES[kind]
    return result


def _families_names(mask):
    return ','.join(name for name,bit in FAMILIES.items() if mask & bit)


def audit_language(conn, language, families, *, tick=None):
    """Exact count for ONE language by scanning index order; bounded memory.

    Equality is a candidate spelling match only, not semantic identity.
    """
    numbers = [0] * 7  # rows, keys, repeated, extra, within-source, across-files, across-families
    ku_kw_uw = [0, 0, 0]
    top = []
    seq = 0
    prev = None
    group_rows = 0
    group_ids = set()
    mask = 0
    inside = False

    def flush():
        nonlocal seq, prev, group_rows, group_ids, mask, inside
        if group_rows == 0:
            return
        numbers[1] += 1
        if group_rows > 1:
            numbers[2] += 1
            numbers[3] += group_rows - 1
        if inside:
            numbers[4] += 1
        if len(group_ids) > 1:
            numbers[5] += 1
        if mask.bit_count() > 1:
            numbers[6] += 1
            if mask & 3 == 3: ku_kw_uw[0] += 1
            if mask & 5 == 5: ku_kw_uw[1] += 1
            if mask & 6 == 6: ku_kw_uw[2] += 1
            # Prioritize cross-family overlap with many observations.
            item = (group_rows, len(group_ids), seq, prev, mask, tuple(sorted(group_ids)[:12]))
            seq += 1
            if len(top) < 8:
                heapq.heappush(top, item)
            elif item[:2] > top[0][:2]:
                heapq.heapreplace(top, item)

    for lemma, sid in conn.execute('''SELECT lemma_key, source_id FROM entries
        INDEXED BY idx_entries_language_lemma WHERE language_code=? ORDER BY lemma_key''', (language,)):
        if prev is not None and lemma != prev:
            flush()
            group_rows = 0
            group_ids = set()
            mask = 0
            inside = False
        prev = lemma
        group_rows += 1
        numbers[0] += 1
        if sid in group_ids:
            inside = True
        else:
            group_ids.add(sid)
        mask |= families[sid]
        if tick is not None and numbers[0] % 250_000 == 0:
            tick(numbers[0])
    flush()
    stats = dict(zip((
        'observation_rows','distinct_lemma_keys','repeated_lemma_keys',
        'extra_observation_rows','repeated_inside_one_source_keys',
        'shared_across_files_keys','shared_across_families_keys'),numbers))
    stats['kaikki_unimorph_keys'],stats['kaikki_wikidata_keys'],stats['unimorph_wikidata_keys'] = ku_kw_uw
    examples = [dict(language_code=language, lemma_key=lemma, observation_rows=count,
                     source_file_count=nsources, family_count=bitmask.bit_count(),
                     family_labels=_families_names(bitmask),
                     source_ids=';'.join(str(sid) for sid in ids))
                for count,nsources,_seq,lemma,bitmask,ids in sorted(top,reverse=True)]
    return stats,examples


def diagnostic_unimorph(root, conn, *, max_rows=2000):
    """Sample *only* small pib/sdh ZIP members, no raw writes or extraction."""
    results=[]
    for edition in FOCUS:
        relative=f'10_sources/lexical/unimorph/repos/{edition}.zip'
        row=conn.execute('''SELECT status,cursor_lines,accepted,rejected
            FROM source_files WHERE relative_path=?''',(relative,)).fetchone()
        archive=(root / relative).resolve()
        item=dict(code=edition, archive_relative=relative,
                  index_status=row[0] if row else 'not_indexed',
                  index_lines=row[1] if row else 0,
                  index_accepted=row[2] if row else 0,
                  index_rejected=row[3] if row else 0,
                  zip_status='absent', total_zip_members=0,
                  possible_data_members=[], member_samples=[],
                  sampled_rows=0, sample_accepted=0, sample_rejected=0,
                  classification='not_checked', warning='')
        if root not in archive.parents:
            item['warning']='Chemin source hors racine; ignoré'
            results.append(item)
            continue
        if not archive.is_file():
            item['classification']='source_missing'
            results.append(item)
            continue
        try:
            with zipfile.ZipFile(archive) as zf:
                item['zip_status']='ok'
                members=zf.infolist()
                item['total_zip_members']=len(members)
                selected=unimorph_members(zf,edition)
                item['possible_data_members']=[dict(name=info.filename,bytes=info.file_size,format=fmt)
                                               for info,fmt in selected[:30]]
                for member,fmt in selected:
                    if item['sampled_rows'] >= max_rows:
                        break
                    preview=[]
                    accepted=0
                    rejected=0
                    with zf.open(member) as file:
                        for bline in file:
                            if item['sampled_rows'] >= max_rows:
                                break
                            item['sampled_rows'] += 1
                            if len(bline)>1_000_000:
                                rejected+=1
                                continue
                            line=bline.decode('utf-8','replace')
                            try:
                                parsed=parse_morph(line,edition,delimiter=',' if fmt=='csv' else '\t')
                            except (ValueError,UnicodeError,csv.Error):
                                parsed=None
                            if parsed:accepted+=1
                            else:rejected+=1
                            if len(preview) < 3:
                                preview.append(line[:150].rstrip().replace('\x00','\\0'))
                    item['sample_accepted']+=accepted
                    item['sample_rejected']+=rejected
                    item['member_samples'].append(dict(member=member.filename,accepted=accepted,
                                                       rejected=rejected,preview=preview))
                if not selected or not any(z.file_size for z,_ in selected):
                    item['classification']='no_nonempty_paradigm'
                elif item['sample_accepted'] > 0 and item['index_status']=='no_data':
                    item['classification']='valid_rows_but_not_indexed'
                elif item['sample_accepted'] > 0:
                    item['classification']='parser_accepts_sample'
                else:
                    item['classification']='parser_rejects_sample'
        except (OSError,zipfile.BadZipFile,RuntimeError,ValueError) as exc:
            item['zip_status']='error'
            item['classification']='zip_error'
            item['warning']=str(exc)[:300]
        results.append(item)
    return results


def write_diagnostic(outdir,diagnostics):
    outdir.mkdir(parents=True,exist_ok=True)
    atomic_json(outdir/'UNIMORPH_PIB_SDH.json',dict(generated_at=utc(),
        method='First N source rows sampled per ZIP, no extraction and no source writes',
        results=diagnostics))
    lines=['# Diagnostic ciblé UniMorph — pib et sdh','','Analyse des ZIP d’origine, lecture seule.',
           'Le nombre de lignes échantillonnées ne prouve pas l’absence de données ailleurs.','']
    for rec in diagnostics:
        lines += [f'## {rec["code"]}', '',
                  f'- État dans index : `{rec["index_status"]}` ; lignes indexées : {rec["index_accepted"]:,}',
                  f'- ZIP : `{rec["zip_status"]}` ; membres : {rec["total_zip_members"]}',
                  f'- Paradigmes candidats : {len(rec["possible_data_members"])}',
                  f'- Échantillon : {rec["sampled_rows"]:,} lignes ; acceptées {rec["sample_accepted"]:,} ; rejetées {rec["sample_rejected"]:,}',
                  f'- Conclusion : `{rec["classification"]}`', '']
        if rec['warning']:lines.append('Attention : '+rec['warning'])
        for member in rec['member_samples']:
            lines.append(f'- `{member["member"]}` : {member["accepted"]} reconnues / {member["rejected"]} rejetées')
            for example in member['preview']:
                lines.append(f'  - `{example.replace("`", "′")}`')
        lines.append('')
    safe_write(outdir/'DIAGNOSTIC_PIB_SDH.md','\n'.join(lines)+'\n')


def safe_write(path, text):
    tmp=path.with_name(path.name+f'.partial-{os.getpid()}')
    tmp.write_text(text,encoding='utf-8')
    os.replace(tmp,path)


def quality_db(path,source_hash):
    path.parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(path,timeout=30)
    con.execute('PRAGMA journal_mode=WAL')
    con.executescript(QUALITY_SCHEMA)
    with con:
        previous=con.execute('SELECT value FROM metadata WHERE key="source_fingerprint"').fetchone()
        if previous and previous[0]!=source_hash:
            con.close()
            raise ValueError('Audit de provenance différente : relancer dans un nouveau répertoire')
        con.execute('INSERT OR IGNORE INTO metadata(key,value) VALUES (?,?)',('source_fingerprint',source_hash))
        con.execute('INSERT OR IGNORE INTO metadata(key,value) VALUES (?,?)',('profile','encyklopedia.lexical-quality-candidate/v0.4'))
    return con


def save_language(audit,lang,stats,examples):
    with audit:
        audit.execute('''INSERT OR REPLACE INTO language_audit (
          language_code,observation_rows,distinct_lemma_keys,repeated_lemma_keys,
          extra_observation_rows,repeated_inside_one_source_keys,
          shared_across_files_keys,shared_across_families_keys,
          kaikki_unimorph_keys,kaikki_wikidata_keys,unimorph_wikidata_keys,completed_at)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', (lang,*(stats[k] for k in (
            'observation_rows','distinct_lemma_keys','repeated_lemma_keys',
            'extra_observation_rows','repeated_inside_one_source_keys',
            'shared_across_files_keys','shared_across_families_keys',
            'kaikki_unimorph_keys','kaikki_wikidata_keys','unimorph_wikidata_keys')),utc()))
        audit.execute('DELETE FROM overlap_examples WHERE language_code=?',(lang,))
        audit.executemany('''INSERT INTO overlap_examples (
           language_code,lemma_key,observation_rows,source_file_count,family_count,family_labels,source_ids)
           VALUES (:language_code,:lemma_key,:observation_rows,:source_file_count,:family_count,:family_labels,:source_ids)''',examples)


def export_reports(root, index, quality, *, signature, all_langs, run_dir, diagnostic, duration=None):
    audited=quality.execute('SELECT COUNT(*) FROM language_audit').fetchone()[0]
    complete=(audited==len(all_langs))
    stats_headers=['language_code','observation_rows','distinct_lemma_keys',
        'repeated_lemma_keys','extra_observation_rows','repeated_inside_one_source_keys',
        'shared_across_files_keys','shared_across_families_keys',
        'kaikki_unimorph_keys','kaikki_wikidata_keys','unimorph_wikidata_keys','completed_at']
    data=list(quality.execute('''SELECT language_code,observation_rows,distinct_lemma_keys,
          repeated_lemma_keys,extra_observation_rows,repeated_inside_one_source_keys,
          shared_across_files_keys,shared_across_families_keys,
          kaikki_unimorph_keys,kaikki_wikidata_keys,unimorph_wikidata_keys,completed_at
          FROM language_audit ORDER BY language_code'''))
    rows=[dict(zip(stats_headers,x)) for x in data]
    atomic_csv(run_dir/'languages_quality.csv',stats_headers,rows)
    pairs=list(quality.execute('''SELECT language_code,lemma_key,observation_rows,
        source_file_count,family_count,family_labels,source_ids FROM overlap_examples
        ORDER BY observation_rows DESC, language_code, lemma_key LIMIT 400'''))
    ex_cols=['language_code','lemma_key','observation_rows','source_file_count','family_count','family_labels','source_ids','source_paths_sample']
    source_names={sid:rel for sid,rel in index.execute('SELECT id,relative_path FROM source_files')}
    sample_rows=[]
    for p in pairs:
        row=dict(zip(ex_cols[:-1],p))
        row['source_paths_sample']='; '.join(source_names.get(int(sid),'?') for sid in row['source_ids'].split(';') if sid)
        sample_rows.append(row)
    atomic_csv(run_dir/'overlap_examples.csv',ex_cols,sample_rows)
    issues=[]
    for x in index.execute('''SELECT relative_path,kind,edition,status,cursor_lines,accepted,rejected,
        COALESCE(error,'') FROM source_files ORDER BY relative_path'''):
        path,kind,edition,state,cursor,accepted,rejected,error=x
        rejection = rejected/max(1, accepted+rejected)
        if state!='complete' or rejection >= 0.05:
            issues.append(dict(relative_path=path,kind=kind,edition=edition,status=state,
                cursor_lines=cursor,accepted=accepted,rejected=rejected,rejection_pct=round(100*rejection,2),error=error))
    issue_cols=['relative_path','kind','edition','status','cursor_lines','accepted','rejected','rejection_pct','error']
    atomic_csv(run_dir/'source_issues.csv',issue_cols,issues)
    sums={k:sum(r[k] for r in rows) for k in stats_headers[1:-1]}
    metadata=dict(profile='encyklopedia.lexical-quality-candidate/v0.4',generated_at=utc(),
        source_database=str(root/SUBDIR/'lexical.sqlite3'), quality_database=str(run_dir/'quality.sqlite3'),
        source_catalog_fingerprint=signature,complete=complete,
        languages_total=len(all_langs),languages_audited=audited,
        data_scope='all_indexed_lemmas' if complete else 'audited_languages_only',
        totals_for_audited_languages=sums,
        audited_source_statuses=dict(Counter(r[0] for r in index.execute('SELECT status FROM source_files'))),
        provenance='read-only lexical index and pib/sdh ZIP diagnostics; derived candidate analytics',
        lemma_definition='(language_code, NFKC casefold lemma_key) in v0.3 index, not semantic lexemes',
        overlap_definition='equal spelling key within language appearing in distinct source files/families; not exactMatch',
        source_sha256_verified=False,source_licenses_reviewed=False,
        canonical_dictionary=False,wikidata_exactmatch_created=False,published=False,
        tik_dik_handoff='candidate audit only; no writes to diK / Kristal',
        diagnostic_results=diagnostic)
    atomic_json(run_dir/'latest.json',metadata)
    lines=['# Audit de qualité lexicale EncyKlopedia — candidat v0.4','',
        f'Généré : {metadata["generated_at"]}',
        f'Index : `{metadata["source_database"]}`','',
        f'**État : {"COMPLET" if complete else "PARTIEL"} — {audited:,}/{len(all_langs):,} codes de langues audités.**','',
        '## Mesures pour les langues déjà auditées','',
        '| Métrique | Compte |','|---|---:|']
    labels=[('observation_rows','Observations de lemmes analysées'),
        ('distinct_lemma_keys','Clés de lemmes distinctes'),
        ('extra_observation_rows','Observations au-delà de la première clé'),
        ('repeated_lemma_keys','Clés répétées'),
        ('repeated_inside_one_source_keys','Clés répétées dans un même fichier source'),
        ('shared_across_files_keys','Clés présentes dans plusieurs fichiers sources'),
        ('shared_across_families_keys','Clés communes à plusieurs familles de sources'),
        ('kaikki_unimorph_keys','Clés communes Kaikki–UniMorph'),
        ('kaikki_wikidata_keys','Clés communes Kaikki–Wikidata'),
        ('unimorph_wikidata_keys','Clés communes UniMorph–Wikidata')]
    lines += [f'| {label} | {sums[k]:,} |' for k,label in labels]
    lines += ['', '## Langues avec le plus de clés communes entre familles','',
        '| Langue | Observations | Clés distinctes | Plusieurs familles |', '|---|---:|---:|---:|']
    for x in sorted(rows,key=lambda z:z['shared_across_families_keys'],reverse=True)[:30]:
        lines.append(f'| {x["language_code"]} | {x["observation_rows"]:,} | {x["distinct_lemma_keys"]:,} | {x["shared_across_families_keys"]:,} |')
    lines += ['', '## pib / sdh','']
    for x in diagnostic:
        lines.append(f'- `{x["code"]}` : `{x["classification"]}`, ZIP `{x["zip_status"]}`, '
                     f'{x["sample_accepted"]} lignes reconnues sur {x["sampled_rows"]} échantillonnées; '
                     f'statut index `{x["index_status"]}`.')
    lines += ['', '## Sources à surveiller','',
        f'{len(issues)} sources ont un statut différent de `complete` ou au moins 5 % de lignes rejetées. Voir `source_issues.csv`.','',
        '## Interprétation et gouvernance','',
        '- Chaque « lemme distinct » est une **clé graphique normalisée par langue**, pas un sens ni un lexème canonique.',
        '- Une répétition au sein d’UniMorph peut correspondre à plusieurs flexions légitimes.',
        '- Les chevauchements Kaikki/UniMorph/Wikidata sont des **candidats homographes**, pas des équivalences sémantiques.',
        '- Les observations des langues non encore auditées ne sont **pas incluses** dans les totaux partiels.',
        '- Aucun SHA-256 n’est validé contre l’éditeur et les licences restent non revues.',
        '- Sources brutes et base lexicale d’origine restent en lecture seule. Aucun KQ/KP ni `exactMatch` créé.',
        '- Publication EncyKlopedia et transfert canonique diK bloqués jusqu’aux revues humaines.','']
    safe_write(run_dir/'RAPPORT_QUALITE_LEXICALE.md','\n'.join(lines))
    return metadata


def perform_audit(root, *, languages=None, min_free_gb=2.0, quiet=False):
    index_path=root/SUBDIR/'lexical.sqlite3'
    quality_root=root/QUALITY_SUBDIR
    with closing(readonly_connection(index_path)) as index:
        source_hash=db_fingerprint(index)
        known=candidates(index)
        expected_counts=dict(known)
        fam=source_families(index)
        known_codes={x[0] for x in known}
        target=set(languages) if languages else known_codes
        unknown=target-known_codes
        if unknown:raise ValueError('Codes de langues absents de l’index: '+', '.join(sorted(unknown)))
        run_dir=quality_root/'runs'/source_hash[:20]
        run_dir.mkdir(parents=True,exist_ok=True)
        with exclusive_lock(run_dir/'audit.lock'):
            with closing(quality_db(run_dir/'quality.sqlite3',source_hash)) as quality:
                seen={row[0] for row in quality.execute('SELECT language_code FROM language_audit')}
                to_do=sorted(target-seen)
                print(f'INDEX: {len(known)} codes; {len(seen)} audités au préalable; {len(to_do)} à traiter',flush=True)
                baseline=index.execute('PRAGMA data_version').fetchone()[0]
                for idx, lang in enumerate(to_do, 1):
                    if shutil.disk_usage(quality_root).free < min_free_gb*1024**3:
                        raise RuntimeError('Espace disque insuffisant pour les rapports qualité')
                    if index.execute('PRAGMA data_version').fetchone()[0]!=baseline:
                        raise RuntimeError('Index lexical modifié simultanément. Audit arrêté pour éviter une vue incohérente.')
                    print(f'LANGUAGE {idx}/{len(to_do)} {lang}',flush=True)
                    summary, examples = audit_language(index,lang,fam, tick=(lambda n: print(f'  {lang}: {n:,} lignes lues',flush=True)))
                    if index.execute('PRAGMA data_version').fetchone()[0]!=baseline:
                        raise RuntimeError('Index lexical modifié pendant la langue '+lang+'; résultat ignoré.')
                    expected=expected_counts[lang]
                    if summary['observation_rows'] != expected:
                        raise RuntimeError(f'Désaccord comptable pour {lang}: entries={summary["observation_rows"]}, language_stats={expected}; langue non enregistrée')
                    save_language(quality,lang,summary,examples)
                    done=len(seen)+idx
                    print(f'PROGRESS|{done}|{len(known)}|{lang}',flush=True)
                    if not quiet and idx%100==0:
                        print(f'Checkpoint: {done}/{len(known)} langues',flush=True)
                if db_fingerprint(index)!=source_hash:
                    raise RuntimeError('Index lexical modifié pendant l’audit; relancer pour une nouvelle capture.')
                diagnostic=diagnostic_unimorph(root,index)
                write_diagnostic(run_dir,diagnostic)
                metadata=export_reports(root,index,quality,signature=source_hash,
                    all_langs=known,run_dir=run_dir,diagnostic=diagnostic)
                atomic_json(quality_root/'latest.json',dict(
                    profile=metadata['profile'],generated_at=metadata['generated_at'],
                    snapshot=source_hash[:20],run_dir=str(run_dir),
                    report=str(run_dir/'RAPPORT_QUALITE_LEXICALE.md'),
                    complete=metadata['complete'],languages_total=len(known),
                    languages_audited=metadata['languages_audited']))
                print(json.dumps(dict(complete=metadata['complete'],audited=metadata['languages_audited'],
                    total=metadata['languages_total'],report=str(run_dir/'RAPPORT_QUALITE_LEXICALE.md')),
                    ensure_ascii=False,indent=2),flush=True)
                return metadata


def main(argv=None):
    ap=argparse.ArgumentParser(description='Audit de qualité lexical en lecture seule; résultats sur D:')
    ap.add_argument('command',choices=['audit','diagnostic','status'])
    ap.add_argument('--data-root',default=os.environ.get('ENCYK_DATA_ROOT',r'D:\EncyKlopedia' if os.name=='nt' else None))
    ap.add_argument('--languages',help='Pilotage: langues séparées par virgules (sinon audit complet)')
    ap.add_argument('--min-free-gb',type=float,default=2.0)
    args=ap.parse_args(argv)
    if not args.data_root:ap.error('--data-root obligatoire')
    if args.min_free_gb<0:ap.error('--min-free-gb invalide')
    root=valid_lake(Path(args.data_root))
    if args.command=='status':
        pointer=root/QUALITY_SUBDIR/'latest.json'
        print(pointer.read_text(encoding='utf-8') if pointer.is_file() else 'Aucun audit qualité encore terminé.')
        return 0
    if args.command=='diagnostic':
        with closing(readonly_connection(root/SUBDIR/'lexical.sqlite3')) as index:
            diag=diagnostic_unimorph(root,index)
        dirname=root/QUALITY_SUBDIR
        write_diagnostic(dirname,diag)
        print(json.dumps(diag,ensure_ascii=False,indent=2))
        print(f'DIAGNOSTIC: {dirname/"DIAGNOSTIC_PIB_SDH.md"}',flush=True)
        return 0
    langs=[x.strip() for x in args.languages.split(',') if x.strip()] if args.languages else None
    perform_audit(root,languages=langs,min_free_gb=args.min_free_gb)
    return 0


if __name__=='__main__':
    try:
        sys.exit(main())
    except (OSError,ValueError,sqlite3.Error,RuntimeError) as exc:
        print(f'ERREUR: {exc}',file=sys.stderr,flush=True)
        sys.exit(1)
