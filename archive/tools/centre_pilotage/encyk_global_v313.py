"""Supervision ENCYKLOPEDIA v31.3 — read-only metrics from existing SQLite files.

Never mutates any of the production databases. Exposes summaries, not Kristal
claim text, quotations, or private payloads. Can run independently of the GUI.
"""
from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

ROOT = Path(r'D:\EncyKlopedia')
DEFAULT_PATHS = {
    'station': ROOT / '30_working' / 'poste_chatgpt_v30' / 'station_v30.sqlite',
    'catalogue': ROOT / '80_search_indexes' / 'EncyKlopedia' / 'catalogue_global_unesco_wikipedia_v25.sqlite',
    'decouverte': ROOT / '30_working' / 'decouverte_articles_relies_v28' / 'DECOUVERTE_ARTICLES_RELIES_V28.sqlite',
    'kristal': ROOT / '30_working' / 'production_kristals_v27' / 'KRISTAL_CUMULATIF_PRIVE_V27.sqlite',
    'packs': ROOT / '30_working' / 'production_kristals_v27' / 'FILE_PACKS_V27.sqlite',
}
SCHEMA = 'encyklopedia.supervision-globale.v31.3-readonly/1'


def source_meta(path: Path) -> dict:
    path = Path(path)
    if not path.is_file():
        return {'available': False, 'path': str(path)}
    st = path.stat()
    # The WAL is deliberately not opened or copied; its presence is recorded.
    wal = Path(str(path) + '-wal')
    return {'available': True, 'path': str(path), 'size_bytes': st.st_size,
            'modified_utc': datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
            'wal_present': wal.exists(),
            'wal_bytes': wal.stat().st_size if wal.exists() else None}


@contextmanager
def open_ro(path: Path):
    path = Path(path)
    if not path.is_file():
        yield None
        return
    # immutable=1 is intentionally absent: it could miss live WAL transactions.
    con = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=10)
    try:
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA query_only=ON')
        yield con
    finally:
        con.close()


def table_exists(con, table: str) -> bool:
    return con.execute('SELECT 1 FROM sqlite_master WHERE type=? AND name=?', ('table', table)).fetchone() is not None


def columns(con, table: str) -> set[str]:
    # table is a private literal only, never a user provided identifier.
    if not table_exists(con, table):
        return set()
    return {r['name'] for r in con.execute('PRAGMA table_info("' + table + '")')}


def count(con, table: str, mandatory: tuple[str, ...] = ()) -> int | None:
    if not set(mandatory).issubset(columns(con, table)):
        return None
    if not table_exists(con, table):
        return None
    return int(con.execute('SELECT COUNT(*) FROM "' + table + '"').fetchone()[0])


def group(con, table: str, col: str, required: tuple[str, ...] = ()) -> dict[str, int] | None:
    if not set((*required, col)).issubset(columns(con, table)):
        return None
    sql = 'SELECT "' + col + '", COUNT(*) FROM "' + table + '" GROUP BY "' + col + '"'
    return {str(r[0]) if r[0] is not None else 'NULL': int(r[1]) for r in con.execute(sql)}


def summarize(paths: dict[str, Path], branch='unesco.mt1.10') -> dict:
    """Summarize real live data, without estimating encyclopedic completion."""
    p = {k: Path(paths[k]) for k in DEFAULT_PATHS}
    result = {
        'schema': SCHEMA,
        'created_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'branch_id': branch,
        'sources': {k: source_meta(v) for k, v in p.items()},
        'station': {}, 'catalogue': {}, 'decouverte': {},
        'kristal_prive': {}, 'packs_kristal': {}, 'alertes': [],
        'achevement_reel_pct': None,
        'sources_coherentes_meme_generation': None,
        'verification_saturation': None,
    }
    errors = result['alertes']

    def load(name, action):
        try:
            with open_ro(p[name]) as con:
                if con is None:
                    errors.append('SOURCE_ABSENTE:' + name)
                else:
                    action(con)
        except (OSError, sqlite3.Error) as e:
            errors.append('LECTURE_IMPOSSIBLE:' + name + ':' + type(e).__name__)

    def station(con):
        s = result['station']
        jcols = columns(con, 'jobs')
        if {'kind', 'status'}.issubset(jcols):
            for r in con.execute('SELECT kind,status,COUNT(*) n FROM jobs GROUP BY kind,status'):
                s.setdefault('jobs_par_type', {}).setdefault(str(r['kind']), {})[str(r['status'])] = int(r['n'])
            s['jobs_total'] = sum(sum(v.values()) for v in s['jobs_par_type'].values())
            s['jobs_ready'] = sum(v.get('READY', 0) for v in s['jobs_par_type'].values())
            s['jobs_ouverts'] = sum(sum(n for k, n in v.items() if k not in ('DONE', 'CANCELLED'))
                                    for v in s['jobs_par_type'].values())
        else:
            errors.append('SCHEMA_INCOMPLET:station.jobs')
        rcols = columns(con, 'review_index')
        if {'branch_id', 'state'}.issubset(rcols):
            s['revue_etats'] = {str(r['state']): int(r['n']) for r in con.execute(
                'SELECT state,COUNT(*) n FROM review_index WHERE branch_id=? GROUP BY state', (branch,))}
        s['postes_assignes'] = int(con.execute('SELECT COUNT(*) FROM lanes WHERE job_id IS NOT NULL').fetchone()[0]) if {'job_id'}.issubset(columns(con,'lanes')) else None
        s['receipts_total'] = count(con, 'receipts')

    def catalogue(con):
        s = result['catalogue']
        s['articles'] = count(con, 'articles')
        if {'branch_id', 'concept_id'}.issubset(columns(con, 'branch_concepts')):
            s['concepts_configures'] = int(con.execute('SELECT COUNT(DISTINCT concept_id) FROM branch_concepts WHERE branch_id=?', (branch,)).fetchone()[0])
        if {'branch_id', 'concept_id', 'page_id'}.issubset(columns(con,'assignments')):
            s['affectations'] = int(con.execute('SELECT COUNT(*) FROM assignments WHERE branch_id=?', (branch,)).fetchone()[0])
        if {'branch_id', 'decision'}.issubset(columns(con, 'reviewed_article_links_v28')):
            s['decisions_importees'] = {str(r[0]): int(r[1]) for r in con.execute(
                'SELECT UPPER(decision), COUNT(*) FROM reviewed_article_links_v28 WHERE branch_id=? GROUP BY UPPER(decision)', (branch,))}

    def discovery(con):
        s = result['decouverte']
        if {'branch_id', 'page_id', 'concept_id'}.issubset(columns(con, 'candidates')):
            s['paires_decouvertes'] = int(con.execute('SELECT COUNT(*) FROM candidates WHERE branch_id=?', (branch,)).fetchone()[0])
        if {'branch_id', 'state'}.issubset(columns(con, 'seed_queue')):
            s['graines_par_etat'] = {str(r[0]): int(r[1]) for r in con.execute(
                'SELECT state,COUNT(*) FROM seed_queue WHERE branch_id=? GROUP BY state', (branch,))}

    def kristal(con):
        s = result['kristal_prive']
        for tab in ('claims', 'citations', 'article_visits', 'delta_imports'):
            s[tab] = count(con, tab)
        s['claims_par_source_status'] = group(con, 'claims', 'source_status')

    def packs(con):
        s = result['packs_kristal']
        s['packs_prepares'] = count(con, 'packs')
        s['articles_par_etat'] = group(con, 'queue', 'state')
        s['changements_epoque_source'] = count(con, 'source_epoch_history')

    for name, action in [('station', station), ('catalogue', catalogue), ('decouverte', discovery),
                         ('kristal', kristal), ('packs', packs)]:
        load(name, action)
    if result['station'].get('jobs_ready', 0):
        errors.append('TACHES_READY_A_CONSERVER:' + str(result['station']['jobs_ready']))
    holds = (result['station'].get('revue_etats') or {}).get('HOLD', 0)
    if holds:
        errors.append('HOLD_A_CONSERVER:' + str(holds))
    if result['sources']['decouverte'].get('available') and result['sources']['catalogue'].get('available'):
        errors.append('SATURATION_NON_DEMONTREE:aucune campagne indépendante de rappel')
    return result
