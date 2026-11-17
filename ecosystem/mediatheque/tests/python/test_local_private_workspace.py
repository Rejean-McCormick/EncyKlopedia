\
from __future__ import annotations
from pathlib import Path
from koa_mediatheque.db import get_db_connection, initialize_database
from koa_mediatheque.services.local_workspace_service import load_local_workspace_config, plan_local_workspace, index_private_documents
from koa_mediatheque.services.kristal_catalog_service import register_kristal_corpus, get_kristal_catalog_stats

def test_private_workspace_plan_and_index(tmp_path: Path):
    docs=tmp_path/"private_docs"; docs.mkdir(); (docs/"note.txt").write_text("secret local note",encoding="utf-8")
    kristals=tmp_path/"kristals"; k=kristals/"Kristal-Test"; k.mkdir(parents=True); (k/"README.md").write_text("# Test Kristal\n",encoding="utf-8")
    cfg=tmp_path/"config.private.toml"; cfg.write_text('[workspace]\nmode="local_private"\nkristal_roots=["kristals"]\ndocument_roots=["private_docs"]\n',encoding="utf-8")
    c=load_local_workspace_config(cfg); plan=plan_local_workspace(c)
    assert plan["kristal_count"]==1; assert plan["document_count"]==1

def test_private_document_defaults_are_non_exportable(tmp_path: Path, schema_dir: Path):
    db=tmp_path/"test.sqlite"; result=initialize_database(db,schema_dir); assert result.success
    f=tmp_path/"private.txt"; f.write_text("private",encoding="utf-8")
    con=get_db_connection(db)
    try:
        stats=index_private_documents(con,[f]); assert stats["inserted"]==1
        row=con.execute("SELECT public_state,visibility,access_level,target_system,export_to_uckk,export_to_public,storage_path FROM library_rows").fetchone()
        assert tuple(row)==("private","private","private","none","no","no",None)
    finally:
        con.close()

def test_register_local_kristal_without_uckk_tables(tmp_path: Path, schema_dir: Path):
    db=tmp_path/"test.sqlite"; assert initialize_database(db,schema_dir).success
    root=tmp_path/"Kristal-Local"; root.mkdir(); (root/"README.md").write_text("# Local\n",encoding="utf-8")
    con=get_db_connection(db)
    try:
        result=register_kristal_corpus(con,root); assert result.success
        assert get_kristal_catalog_stats(con)["kristals"]==1
        names={r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "kristal_publications" not in names
    finally:
        con.close()
