import importlib.util
import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

MODULE = Path(__file__).parents[1] / 'tools' / 'dik_federation_preflight.py'
spec = importlib.util.spec_from_file_location('dik_federation_preflight', MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def sample(tmp_path):
    folder=tmp_path/'view';folder.mkdir()
    dbfile=folder/'registry.sqlite3'
    with sqlite3.connect(dbfile) as db:
        db.execute('CREATE TABLE kristals(kristal TEXT,state TEXT)')
        db.execute("INSERT INTO kristals VALUES ('alpha','EVALUABLE')")
        db.execute('CREATE TABLE identities(kristal TEXT,namespace_id TEXT,semantic_id TEXT)')
        db.execute('CREATE TABLE crosswalk(namespace_id TEXT,semantic_id TEXT,wikidata_id TEXT,decision TEXT)')
    m={'profile':mod.PROFILE,'purpose':'read_only_derived_index_not_canonical',
       'status':'CANDIDATE_FEDERATED_VIEW','sqlite_file':'registry.sqlite3',
       'sqlite_sha256':hashlib.sha256(dbfile.read_bytes()).hexdigest(),
       'languages_target':mod.LANGS,'automatic_approvals':0,'published_dictionaries':0,
       'new_semantic_authority_created':False,'legacy_no_retained':True,
       'statistics':{'official_kristals':1,'local_kq_kp_occurrences':0}}
    (folder/'manifest.json').write_text(json.dumps(m))
    return folder


def test_valid_integrity_never_publication(tmp_path):
    r=mod.preflight(sample(tmp_path))
    assert r['validation']=='INTEGRITY_ONLY'
    assert r['publication_authorized'] is False
    assert r['new_runtime_set_authorized'] is False


def test_tamper_rejected(tmp_path):
    folder=sample(tmp_path)
    (folder/'registry.sqlite3').write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='digest'):
        mod.preflight(folder)


def test_forged_permission_rejected(tmp_path):
    folder=sample(tmp_path)
    p=folder/'manifest.json'; m=json.loads(p.read_text());m['automatic_approvals']=1
    p.write_text(json.dumps(m))
    with pytest.raises(ValueError,match='authority'):
        mod.preflight(folder)
