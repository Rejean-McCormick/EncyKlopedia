from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_builder(project_root: Path):
    path = project_root / "mediatheque" / "05_TOOLS" / "Build-UckkBootstrapManifest.py"
    spec = importlib.util.spec_from_file_location("uckk_bootstrap_builder", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_packaged_uckk_bootstrap_is_complete() -> None:
    package_root = Path(__file__).resolve().parents[3]
    bootstrap = package_root / "mediatheque-uckk" / "bootstrap"
    plan = json.loads((bootstrap / "import-plan.json").read_text(encoding="utf-8"))

    assert plan["format"] == "koa.mediatheque.uckk-bootstrap/1.1.0"
    assert plan["library"]["slug"] == "uckk"
    assert plan["counts"] == {
        "kristal_artifacts": 111,
        "korpus_media": 64,
        "github_repositories": 58,
        "total_bootstrap_objects": 233,
    }
    assert plan["kristal_contract"]["portable_contract"] == "kristal_state/6.0"
    assert plan["kristal_contract"]["kristall_baseline"] == "7.0.0-draft.3.2"

    refs = {entry["kristal_ref"] for entry in plan["kristals"]}
    assert len(refs) == 111
    assert "urn:uckk:kristal:universite" in refs
    for entry in plan["kristals"]:
        parent = entry["parent_kristal_ref"]
        assert parent is None or parent in refs
        path = bootstrap / "kristals" / entry["source_relative_path"]
        assert path.is_file()


def test_builder_revalidates_packaged_hierarchy() -> None:
    package_root = Path(__file__).resolve().parents[3]
    bootstrap = package_root / "mediatheque-uckk" / "bootstrap"
    builder = _load_builder(package_root)

    kristals, hierarchy = builder.build_kristals(bootstrap / "kristals")
    korpus = builder.build_korpus(bootstrap / "korpus" / "uckk_inventory.json", None)
    repositories, repository_catalog = builder.build_repositories(
        bootstrap / "repositories" / "github-repositories.json"
    )

    assert hierarchy["counts"]["total_kristals"] == 111
    assert len(kristals) == 111
    assert len(korpus) == 64
    assert len(repositories) == 58
    assert repository_catalog["counts"]["commit_pinned_repositories"] == 12
    assert sum(1 for item in kristals if item["kind"] == "university") == 1
    assert sum(1 for item in kristals if item["kind"] == "voie") == 10
    assert sum(1 for item in kristals if item["kind"] == "course") == 100

def test_github_repository_catalog_is_external_and_unique() -> None:
    package_root = Path(__file__).resolve().parents[3]
    path = package_root / "mediatheque-uckk" / "bootstrap" / "repositories" / "github-repositories.json"
    catalog = json.loads(path.read_text(encoding="utf-8"))

    assert catalog["format"] == "koa.mediatheque.github-repository-catalog/1.0.0"
    assert catalog["counts"] == {
        "public_repositories": 58,
        "commit_pinned_repositories": 12,
    }
    urls = [item["github_url"] for item in catalog["repositories"]]
    media_uuids = [item["media_uuid"] for item in catalog["repositories"]]
    assert len(set(urls)) == 58
    assert len(set(media_uuids)) == 58
    assert all(url.startswith("https://github.com/") for url in urls)
    pinned = [item for item in catalog["repositories"] if item.get("pinned_commit")]
    assert len(pinned) == 12
    assert all(
        item.get("pinned_commit_url") == f"{item['github_url'].rstrip('/')}/commit/{item['pinned_commit']}"
        for item in pinned
    )
    assert any(item["repository_name"] == "UCKK" for item in catalog["repositories"])
    assert any(item["repository_name"] == "Kristal-Framework" for item in catalog["repositories"])
    assert any(item["repository_name"] == "Konstellation" for item in catalog["repositories"])

