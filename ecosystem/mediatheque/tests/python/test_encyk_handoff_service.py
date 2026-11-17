"""EncyK producer v2 → Médiathèque consumer tests on disposable local instances."""
from __future__ import annotations

import hashlib
import json
from contextlib import closing
from pathlib import Path

import pytest
from conftest import import_app_callable


def make_handoff(tmp_path: Path, *, scope: str = 'pilot-a', snapshot: str = 'snapshot-1',
                 url: str = 'https://www.wikidata.org/wiki/Special:EntityData',
                 producer_version: str = '0.12.0'):
    root = tmp_path / ('evidence-' + scope)
    root.mkdir(parents=True,exist_ok=True)
    entries = []
    for role, path, content in [
        ('scope_config', 'config/scope.json', b'{"query":"x"}'),
        ('frozen_scope', 'work/scope.freeze.json', b'{"scope":"freeze"}'),
        ('evidence_manifest', 'snap/snapshot-manifest.json', b'{"source":"wikidata"}'),
        ('lossless_source_evidence', 'snap/entities.wikidata.jsonl.gz', b'evidence-0000'),
        ('entity_content_manifest', 'snap/entities.manifest.jsonl', b'{"id":"Q1"}\n'),
    ]:
        target = root/path
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(content)
        entries.append({'role':role,'path':path,'bytes':len(content),
                        'sha256':'sha256:'+hashlib.sha256(content).hexdigest()})
    data={
        'schema_version':'encyk-source-evidence-handoff/v2',
        'contract':'encyk.source-evidence-handoff/2.0.0',
        'producer':{'system':'encyk','version':producer_version},
        'consumer':{'system':'koa-mediatheque','minimum_version':'0.2.0',
                    'source_catalog_profile':'koa.source-catalog/2.0.0'},
        'scope_key':scope,'snapshot_id':snapshot,'source_system':'wikidata',
        'source_descriptor':{'external_source_id':'wikidata:entity-dump','title':'Wikidata entity dump',
            'source_kind':'dataset','source_family':'wikidata','canonical_url':url},
        'source_snapshot':{'dump_id':'wikidata-test'},
        'created_at':'2026-10-08T21:00:00Z','scope_config':entries[0],
        'files':entries[1:],
        'invariants':['External identifiers are source candidates; Médiathèque assigns durable identities.'],
    }
    identity={k:v for k,v in data.items() if k!='created_at'}
    raw=json.dumps(identity,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    data['handoff_id']='handoff-'+hashlib.sha256(raw).hexdigest()[:20]
    mp = root/'handoff.json'
    mp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
    return root,mp,data


def init(tmp_path, project_root):
    initialize=import_app_callable('db','initialize_database')
    get_connection=import_app_callable('db','get_db_connection')
    db=tmp_path/'koa.sqlite'
    result=initialize(db,project_root/'schemas'/'sqlite')
    assert result.success, result
    return get_connection(db)


def test_accept_and_idempotent_replay(tmp_path, project_root):
    imp=import_app_callable('services.encyk_handoff_service','import_encyk_handoff')
    root,mp,_=make_handoff(tmp_path)
    with closing(init(tmp_path,project_root)) as db:
        first=imp(db,mp,root,tmp_path/'02_STORAGE')
        again=imp(db,mp,root,tmp_path/'02_STORAGE')
        assert first['status']=='accepted'
        assert again['status']=='already_accepted'
        assert first['handoff_id']==again['handoff_id']
        assert len(first['representations'])==5
        for t,n in [('source_registry',1),('source_snapshots',1),('source_representations',5),
                    ('library_rows',5),('source_bindings',1),('encyk_handoff_receipts',1)]:
            assert db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]==n
        assert db.execute("SELECT COUNT(*) FROM library_rows WHERE visibility='private' AND export_to_public='no'").fetchone()[0]==5
        assert all(r['locator'].startswith('koa-media://version/') for r in first['representations'])
        assert first['semantic_identity_assigned'] is False


def test_schema_rejects_old_contract(tmp_path):
    plan=import_app_callable('services.encyk_handoff_service','plan_encyk_handoff')
    root,mp,data=make_handoff(tmp_path)
    data['contract']='encyklopedia.corpus-harvest-handoff/1.0.0'
    mp.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='Schema validation'):
        plan(mp,root)


def test_rejects_tampered_manifest_identity(tmp_path):
    plan=import_app_callable('services.encyk_handoff_service','plan_encyk_handoff')
    root,mp,data=make_handoff(tmp_path)
    data['source_descriptor']['title']='new title'
    mp.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='handoff_id'):
        plan(mp,root)


def test_rejects_missing_bytes_before_any_sqlite_write(tmp_path,project_root):
    imp=import_app_callable('services.encyk_handoff_service','import_encyk_handoff')
    root,mp,_=make_handoff(tmp_path)
    (root/'snap/entities.wikidata.jsonl.gz').unlink()
    with closing(init(tmp_path,project_root)) as db:
        with pytest.raises(ValueError,match='missing'):
            imp(db,mp,root,tmp_path/'02_STORAGE')
        assert db.execute('SELECT COUNT(*) FROM source_registry').fetchone()[0]==0


def test_rejects_size_and_sha_mismatch(tmp_path):
    plan=import_app_callable('services.encyk_handoff_service','plan_encyk_handoff')
    root,mp,_=make_handoff(tmp_path)
    (root/'snap/entities.wikidata.jsonl.gz').write_bytes(b'evidence-0001')
    with pytest.raises(ValueError,match='content mismatch'):
        plan(mp,root)


def test_rejects_path_traversal_and_symlink(tmp_path):
    plan=import_app_callable('services.encyk_handoff_service','plan_encyk_handoff')
    root,mp,data=make_handoff(tmp_path)
    entry=data['files'][0]
    entry['path']='../outside.txt'
    identity={k:v for k,v in data.items() if k not in ('created_at','handoff_id')}
    data['handoff_id']='handoff-'+hashlib.sha256(json.dumps(identity,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()[:20]
    mp.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='Unsafe'):
        plan(mp,root)
    # Separate test where a malicious on-disk symlink is swapped for a legitimate file.
    root,mp,_=make_handoff(tmp_path/'other')
    target=root/'work/scope.freeze.json'
    target.unlink()
    try:
        target.symlink_to(root/'snap/snapshot-manifest.json')
    except (OSError, NotImplementedError):
        pytest.skip('Symlinks unavailable on this platform')
    with pytest.raises(ValueError,match='Symlink'):
        plan(mp,root)


def test_dedup_bytes_and_shared_source_across_scopes(tmp_path,project_root):
    imp=import_app_callable('services.encyk_handoff_service','import_encyk_handoff')
    root1,m1,_=make_handoff(tmp_path,scope='one')
    root2,m2,_=make_handoff(tmp_path,scope='two')
    with closing(init(tmp_path,project_root)) as db:
        first=imp(db,m1,root1,tmp_path/'storage')
        second=imp(db,m2,root2,tmp_path/'storage')
        assert first['source_uuid']==second['source_uuid']
        assert first['snapshot_uuid']!=second['snapshot_uuid']
        assert db.execute('SELECT COUNT(*) FROM source_registry').fetchone()[0]==1
        assert db.execute('SELECT COUNT(*) FROM source_snapshots').fetchone()[0]==2
        assert db.execute('SELECT COUNT(*) FROM library_rows').fetchone()[0]==5
        assert db.execute('SELECT COUNT(*) FROM source_representations').fetchone()[0]==10


def test_rejects_conflicting_snapshot_without_matching_receipt(tmp_path,project_root):
    imp=import_app_callable('services.encyk_handoff_service','import_encyk_handoff')
    root,mp,_=make_handoff(tmp_path)
    with closing(init(tmp_path,project_root)) as db:
        imp(db,mp,root,tmp_path/'storage')
        db.execute('DELETE FROM encyk_handoff_receipts')
        db.commit()
        with pytest.raises(ValueError,match='Snapshot already exists'):
            imp(db,mp,root,tmp_path/'storage')


def test_replay_detects_deleted_stored_bytes(tmp_path,project_root):
    imp=import_app_callable('services.encyk_handoff_service','import_encyk_handoff')
    root,mp,_=make_handoff(tmp_path)
    with closing(init(tmp_path,project_root)) as db:
        result=imp(db,mp,root,tmp_path/'storage')
        version=result['representations'][0]['version_uuid']
        row=db.execute('SELECT storage_path FROM library_rows WHERE version_uuid=?',(version,)).fetchone()
        Path(row[0]).unlink()
        with pytest.raises(ValueError,match='Previously stored'):
            imp(db,mp,root,tmp_path/'storage')


def test_cli_plan_accept_replay_and_rejected_receipt(tmp_path, project_root):
    import subprocess
    import sys
    root, mp, _ = make_handoff(tmp_path)
    cli = project_root / '05_TOOLS' / 'ImportEncyKHandoff.py'
    common = [sys.executable, str(cli), '--handoff', str(mp), '--evidence-root', str(root)]
    plan = subprocess.run(common, text=True, capture_output=True)
    assert plan.returncode == 0, plan.stderr
    assert json.loads(plan.stdout)['status'] == 'plan_valid'
    assert not (tmp_path / 'storage').exists()

    with closing(init(tmp_path, project_root)):
        pass
    db_path = tmp_path / 'koa.sqlite'
    accepting = common + ['--accept', '--db', str(db_path), '--storage', str(tmp_path / 'storage')]
    first = subprocess.run(accepting, text=True, capture_output=True)
    assert first.returncode == 0, first.stderr
    assert json.loads(first.stdout)['status'] == 'accepted'
    again = subprocess.run(accepting, text=True, capture_output=True)
    assert again.returncode == 0, again.stderr
    assert json.loads(again.stdout)['status'] == 'already_accepted'

    (root / 'snap/entities.wikidata.jsonl.gz').write_bytes(b'tampered')
    rejected_file = tmp_path / 'receipts' / 'refused.json'
    refused = subprocess.run(common + ['--receipt-out', str(rejected_file)],
                             text=True, capture_output=True)
    assert refused.returncode == 1
    assert json.loads(rejected_file.read_text())['status'] == 'rejected'


def test_current_skope_encyk_014_handoff_and_idempotence(tmp_path, project_root):
    """Skope 1.0 RC1 ships EncyK 0.14.0; no producer downgrade is allowed."""
    imp = import_app_callable('services.encyk_handoff_service', 'import_encyk_handoff')
    root, manifest, _ = make_handoff(tmp_path, producer_version='0.14.0')
    with closing(init(tmp_path, project_root)) as db:
        first = imp(db, manifest, root, tmp_path / '02_STORAGE')
        second = imp(db, manifest, root, tmp_path / '02_STORAGE')
        assert first['status'] == 'accepted'
        assert second['status'] == 'already_accepted'
        assert first['visibility'] == 'private'
        assert not first['semantic_identity_assigned']


def test_future_unapproved_producer_version_is_rejected(tmp_path):
    plan = import_app_callable('services.encyk_handoff_service', 'plan_encyk_handoff')
    root, manifest, _ = make_handoff(tmp_path, producer_version='0.15.0')
    with pytest.raises(ValueError, match='Schema validation'):
        plan(manifest, root)


def test_cli_instance_root_targets_one_existing_library(tmp_path, project_root):
    import subprocess
    import sys
    root, manifest, _ = make_handoff(tmp_path, producer_version='0.14.0')
    instance = tmp_path / 'mediatheque-privee'
    (instance / '01_DB').mkdir(parents=True)
    (instance / '02_STORAGE').mkdir()
    other = tmp_path / 'mediatheque-math'
    (other / '01_DB').mkdir(parents=True)
    (other / '02_STORAGE').mkdir()
    initialize = import_app_callable('db', 'initialize_database')
    assert initialize(instance / '01_DB' / 'koa_mediatheque.sqlite', project_root / 'schemas' / 'sqlite').success
    assert initialize(other / '01_DB' / 'koa_mediatheque.sqlite', project_root / 'schemas' / 'sqlite').success
    cmd = [sys.executable, str(project_root / '05_TOOLS' / 'ImportEncyKHandoff.py'),
           '--handoff', str(manifest), '--evidence-root', str(root)]
    planned = subprocess.run(cmd + ['--instance-root', str(instance)], text=True, capture_output=True)
    assert planned.returncode == 0, planned.stderr
    assert json.loads(planned.stdout)['status'] == 'plan_valid'
    rejected = subprocess.run(cmd + ['--accept', '--instance-root', str(instance),
                                     '--storage', str(other / '02_STORAGE')], text=True, capture_output=True)
    assert rejected.returncode != 0
    assert json.loads(rejected.stderr)['status'] == 'rejected'
    accepted = subprocess.run(cmd + ['--accept', '--instance-root', str(instance)], text=True, capture_output=True)
    assert accepted.returncode == 0, accepted.stderr
    assert json.loads(accepted.stdout)['status'] == 'accepted'
    import sqlite3
    with closing(sqlite3.connect(other / '01_DB' / 'koa_mediatheque.sqlite')) as other_db:
        assert other_db.execute('SELECT COUNT(*) FROM source_registry').fetchone()[0] == 0
    assert list((instance / '02_STORAGE' / 'source_files').iterdir())
    assert not (other / '02_STORAGE' / 'source_files').exists()
    repeated = subprocess.run(cmd + ['--accept', '--instance-root', str(instance)], text=True, capture_output=True)
    assert repeated.returncode == 0, repeated.stderr
    assert json.loads(repeated.stdout)['status'] == 'already_accepted'
