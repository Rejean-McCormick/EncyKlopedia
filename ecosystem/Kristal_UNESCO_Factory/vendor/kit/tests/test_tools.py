import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

KIT = Path(__file__).resolve().parents[1]
CLI = KIT / "tools" / "kristal.py"

spec = importlib.util.spec_from_file_location("kristal_tool", CLI)
kt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kt)


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="kristal-kit-test-"))
        self.ws = self.tmp / "demo"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(CLI), *map(str, args)], capture_output=True, text=True)

    def init(self):
        r = self.run_cli("init", self.ws, "--title", "Demo")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)

    def add_json_artifact(self):
        p = self.ws / "canon/domain/core.json"
        p.write_text(json.dumps({"items": [{"id": "a", "value": 1}, {"id": "b", "value": 2}]}, indent=2) + "\n")
        r = self.run_cli(
            "register-artifact", self.ws,
            "--file", "canon/domain/core.json",
            "--artifact-id", "urn:kristal:demo:core",
            "--contract-id", "demo.core",
        )
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)

    def test_init_and_check_local_v32(self):
        self.init()
        ws = json.loads((self.ws / "kristal.workspace.json").read_text())
        self.assertEqual(ws["format"], "kristal.local-workspace/3.2.0")
        self.assertEqual(ws["target"]["state_architecture"], "kristal.state/9.0")
        self.assertEqual(ws["target"]["hosted_network_baseline"], "kristal.hosting/10.0")
        self.assertEqual(ws["portable_ai"]["profile"], "kristal.portable-ai/1.0")
        self.assertFalse(ws["portable_ai"]["enabled"])
        self.assertFalse((self.ws / "AI_START_HERE.md").exists())
        self.assertEqual(ws["state_ref"], "urn:kristal:state:demo")
        r = self.run_cli("check", self.ws)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)

    def test_init_with_ai_seeds_optional_ai_entrypoint(self):
        r = self.run_cli("init", self.ws, "--title", "Demo", "--with-ai")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        ws = json.loads((self.ws / "kristal.workspace.json").read_text())
        self.assertTrue(ws["portable_ai"]["enabled"])
        self.assertTrue((self.ws / "AI_START_HERE.md").is_file())

    def test_inspect_is_read_only_and_machine_readable(self):
        self.init(); self.add_json_artifact()
        before = (self.ws / "canon/state.index.json").read_bytes()
        self.assertEqual(self.run_cli("build-v9", self.ws).returncode, 0)
        r = self.run_cli("inspect", self.ws)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        obj = json.loads(r.stdout)
        self.assertEqual(obj["format"], "kristal.local-inspection/1.0")
        self.assertEqual(obj["kit_version"], kt.KIT_VERSION)
        self.assertEqual(obj["state"]["kind"], "build_v9")
        self.assertEqual(obj["state"]["path"], "build/v9/state-snapshot.json")
        self.assertEqual(obj["state"]["state_ref"], "urn:kristal:state:demo")
        self.assertEqual(obj["interop"]["suggested_collection_root"], "kristals/demo")
        self.assertEqual(obj["interop"]["suggested_collection_state_path"], "kristals/demo/state/state-snapshot.json")
        self.assertEqual(obj["interop"]["suggested_channel_suffix"], "demo/stable")
        self.assertEqual(obj["github_read_surface"]["format"], "kristal.github-read-surface/1.0")
        self.assertFalse(obj["github_read_surface"]["ready"])
        self.assertEqual(before, (self.ws / "canon/state.index.json").read_bytes())

    def test_inspect_prefers_explicit_state_export(self):
        self.init(); self.add_json_artifact(); self.assertEqual(self.run_cli("build-v9", self.ws).returncode, 0)
        src = self.ws / "build/v9/state-snapshot.json"
        dst = self.ws / "state/state-snapshot.json"
        dst.write_bytes(src.read_bytes())
        r = self.run_cli("inspect", self.ws, "--compact")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        obj = json.loads(r.stdout)
        self.assertEqual(obj["state"]["kind"], "state_export")
        self.assertEqual(obj["state"]["path"], "state/state-snapshot.json")

    def test_check_does_not_warn_about_ai_when_disabled(self):
        self.init(); self.add_json_artifact(); self.assertEqual(self.run_cli("build-v9", self.ws).returncode, 0)
        r = self.run_cli("check", self.ws)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertNotIn("portable AI layer is missing", r.stdout)
        self.assertNotIn("Portable AI is enabled but", r.stdout)

    def test_projection_v3_workspace_preserves_projection_v2(self):
        self.init()
        r = self.run_cli("new-projection", self.ws, "--slug", "main", "--subject-ref", "subject:main", "--primary-axis", "functional")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        obj = json.loads((self.ws / "projections/recipes/main.projection.json").read_text())
        self.assertEqual(obj["format"], "kristal.projection-recipe/2.0.0")
        self.assertEqual(obj["projection_contract"]["relationship_to_v9_canon"], "derived_projection")

    def test_local_tool_is_self_contained(self):
        self.init()
        local = self.ws / "tools" / "kristal.py"
        self.assertTrue(local.exists())
        r = subprocess.run([sys.executable, str(local), "check", str(self.ws)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)

    def test_source_uniqueness(self):
        self.init()
        r = self.run_cli("add-source", self.ws, "--id", "s1", "--title", "Source", "--locator", "external://s1")
        self.assertEqual(r.returncode, 0)
        r = self.run_cli("add-source", self.ws, "--id", "s1", "--title", "Source", "--locator", "external://s1")
        self.assertNotEqual(r.returncode, 0)

    def test_build_v9_logical_and_state_commitments(self):
        self.init(); self.add_json_artifact()
        r = self.run_cli("build-v9", self.ws)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        state = json.loads((self.ws / "build/v9/state-snapshot.json").read_text())
        self.assertEqual(state["artifact_type"], "kristal_state_snapshot")
        self.assertEqual(state["logical_commitment"], kt.state_commitment(state))
        arts = list((self.ws / "build/v9/artifacts").glob("*.json"))
        self.assertEqual(len(arts), 1)
        art = json.loads(arts[0].read_text())
        self.assertEqual(art["logical_commitment"], kt.logical_artifact_commitment(art))
        self.assertEqual(state["members"][0]["logical_commitment"], art["logical_commitment"])

    def test_commitment_invariance_identity_vs_payload(self):
        artifact = {
            "logical_contract": {"id": "demo.core", "version": "1.0"},
            "artifact_id": "urn:a",
            "payload": {"x": 1},
            "authority_ref": "urn:auth:a",
        }
        base = kt.logical_artifact_commitment(artifact)["digest"]
        changed_id = dict(artifact); changed_id["artifact_id"] = "urn:b"
        self.assertEqual(base, kt.logical_artifact_commitment(changed_id)["digest"])
        changed_authority = dict(artifact); changed_authority["authority_ref"] = "urn:auth:b"
        self.assertEqual(base, kt.logical_artifact_commitment(changed_authority)["digest"])
        changed_payload = dict(artifact); changed_payload["payload"] = {"x": 2}
        self.assertNotEqual(base, kt.logical_artifact_commitment(changed_payload)["digest"])

    def test_pinned_reference_is_in_state_commitment(self):
        self.init(); self.add_json_artifact()
        digest = "sha256:" + "1" * 64
        r = self.run_cli("add-reference", self.ws, "--kind", "state", "--id", "urn:kristal:state:child", "--digest", digest)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertEqual(self.run_cli("build-v9", self.ws).returncode, 0)
        state = json.loads((self.ws / "build/v9/state-snapshot.json").read_text())
        base = state["logical_commitment"]["digest"]
        state["references"][0]["logical_commitment"]["digest"] = "sha256:" + "2" * 64
        self.assertNotEqual(base, kt.state_commitment(state)["digest"])

    def test_precomputed_non_json_artifact_preserves_polymorphism(self):
        self.init()
        p = self.ws / "canon/domain/model.native"; p.write_bytes(b"native-format\x00payload")
        digest = "sha256:" + "a" * 64
        r = self.run_cli(
            "register-artifact", self.ws, "--file", "canon/domain/model.native",
            "--artifact-id", "urn:kristal:demo:native", "--contract-id", "demo.native",
            "--mode", "precomputed", "--commitment-profile", "demo.logical/native-v1", "--digest", digest,
        )
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertEqual(self.run_cli("build-v9", self.ws).returncode, 0)
        state = json.loads((self.ws / "build/v9/state-snapshot.json").read_text())
        self.assertEqual(state["members"][0]["logical_commitment"]["digest"], digest)
        self.assertEqual(len(list((self.ws / "build/v9/artifacts").glob("*.json"))), 0)

    def test_custom_materialization_is_preserved_and_advertised(self):
        self.init(); self.add_json_artifact()
        idx = json.loads((self.ws / "canon/state.index.json").read_text())
        ref = kt._canonical_ref_map(self.ws, idx)["urn:kristal:demo:core"]
        blobs = self.ws / "materializations/v9/blobs"; blobs.mkdir(parents=True)
        a = blobs / "a.bin"; b = blobs / "b.bin"
        a.write_bytes(b"alpha-alpha-alpha")
        b.write_bytes(b"beta-beta-beta")
        manifest = {
            "schema_version": "9.0",
            "artifact_type": "kristal_materialization_manifest",
            "materialization_id": "urn:kristal:materialization:demo:factorized",
            "source": ref,
            "profile": "demo.materialization/factorized-zstd/1",
            "partition_spec": {"strategy": "fixed-record-count"},
            "segments": [
                {"segment_key": "a", "record_count": 1, "blob": {"media_type": "application/octet-stream", "digest": "sha256:" + kt.hash_file(a), "size": a.stat().st_size, "locator": "materializations/v9/blobs/a.bin"}},
                {"segment_key": "b", "record_count": 1, "blob": {"media_type": "application/octet-stream", "digest": "sha256:" + kt.hash_file(b), "size": b.stat().st_size, "locator": "materializations/v9/blobs/b.bin"}},
            ],
            "reconstructability": {"lossless": True, "profile": "demo.core/1.0"},
            "extensions": {"capabilities": {"factorization": True}},
        }
        src = self.tmp / "factorized.json"; src.write_text(json.dumps(manifest, indent=2) + "\n")
        r = self.run_cli("register-materialization", self.ws, "--manifest", src)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertEqual(self.run_cli("check", self.ws).returncode, 0)
        r = self.run_cli("build-v9", self.ws)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        caps = json.loads((self.ws / "build/v9/v9-capabilities.json").read_text())
        mat = caps["capabilities"]["materialization"]
        self.assertIn("kristal.materialization/inline-json/1", mat["profiles"])
        self.assertIn("demo.materialization/factorized-zstd/1", mat["profiles"])
        self.assertTrue(mat["segmentation"])
        self.assertTrue(mat["factorization"])
        imported = list((self.ws / "build/v9/materializations").glob("imported-*.materialization.json"))
        self.assertEqual(len(imported), 1)
        self.assertEqual(json.loads(imported[0].read_text())["materialization_id"], manifest["materialization_id"])

    def test_legacy_materialization_capability_hint_is_preserved(self):
        self.init(); self.add_json_artifact()
        idx = json.loads((self.ws / "canon/state.index.json").read_text())
        ref = kt._canonical_ref_map(self.ws, idx)["urn:kristal:demo:core"]
        legacy = self.ws / ".kristal/v9/materializations"; legacy.mkdir(parents=True)
        blob = self.ws / ".kristal/v9/blob.bin"; blob.parent.mkdir(parents=True, exist_ok=True); blob.write_bytes(b"factorized")
        profile = "demo.materialization/domain-factorized/1"
        manifest = {
            "schema_version": "9.0", "artifact_type": "kristal_materialization_manifest",
            "materialization_id": "urn:kristal:materialization:demo:legacy",
            "source": ref, "profile": profile,
            "segments": [{"segment_key": "all", "record_count": 1, "blob": {"media_type": "application/octet-stream", "digest": "sha256:" + kt.hash_file(blob), "size": blob.stat().st_size, "locator": ".kristal/v9/blob.bin"}}],
            "reconstructability": {"lossless": True, "profile": "demo.core/1.0"},
        }
        (legacy / "custom.json").write_text(json.dumps(manifest, indent=2) + "\n")
        caps = {
            "schema_version": "9.0", "artifact_type": "kristal_v9_capabilities",
            "compatibility": {"reads": ["kristal_state/6.0", "kristall/7.0", "kristall/8.0", "kristal.state/9.0"], "portable_state": "kristal_state/6.0", "semantic_baseline": "kristall/7.0", "query_baseline": "kristall/8.0"},
            "capabilities": {"state_architecture": {"logical_artifacts": True, "immutable_snapshots": True, "logical_commitments": True}, "materialization": {"profiles": [profile], "multiple_representations": True, "segmentation": False, "factorization": True}, "lifecycle": {"build_publish_activate": True, "atomic_activation": True}},
        }
        (self.ws / ".kristal/v9/capabilities.json").write_text(json.dumps(caps, indent=2) + "\n")
        r = self.run_cli("build-v9", self.ws)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        built = json.loads((self.ws / "build/v9/v9-capabilities.json").read_text())
        self.assertTrue(built["capabilities"]["materialization"]["factorization"])
        self.assertIn(profile, built["capabilities"]["materialization"]["profiles"])

    def test_materialization_binding_mismatch_fails_check(self):
        self.init(); self.add_json_artifact()
        idx = json.loads((self.ws / "canon/state.index.json").read_text())
        ref = kt._canonical_ref_map(self.ws, idx)["urn:kristal:demo:core"]
        ref["logical_commitment"] = {"profile": kt.LOGICAL_PROFILE, "digest": "sha256:" + "0" * 64}
        d = self.ws / "materializations/v9/manifests"; d.mkdir(parents=True, exist_ok=True)
        blob = self.ws / "materializations/v9/b.bin"; blob.write_bytes(b"x")
        manifest = {
            "schema_version": "9.0", "artifact_type": "kristal_materialization_manifest",
            "materialization_id": "urn:kristal:materialization:demo:bad-binding", "source": ref,
            "profile": "kristal.materialization/native-blob/1",
            "segments": [{"segment_key": "all", "blob": {"media_type": "application/octet-stream", "digest": "sha256:" + kt.hash_file(blob), "size": 1, "locator": "materializations/v9/b.bin"}}],
            "reconstructability": {"lossless": True},
        }
        (d / "bad.json").write_text(json.dumps(manifest, indent=2) + "\n")
        r = self.run_cli("check", self.ws)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("logical_commitment does not match", r.stdout)

    def test_materialization_local_blob_digest_mismatch_fails_check(self):
        self.init(); self.add_json_artifact()
        idx = json.loads((self.ws / "canon/state.index.json").read_text())
        ref = kt._canonical_ref_map(self.ws, idx)["urn:kristal:demo:core"]
        d = self.ws / "materializations/v9/manifests"; d.mkdir(parents=True, exist_ok=True)
        blob = self.ws / "materializations/v9/b.bin"; blob.write_bytes(b"actual")
        manifest = {
            "schema_version": "9.0", "artifact_type": "kristal_materialization_manifest",
            "materialization_id": "urn:kristal:materialization:demo:bad-blob", "source": ref,
            "profile": "kristal.materialization/native-blob/1",
            "segments": [{"segment_key": "all", "blob": {"media_type": "application/octet-stream", "digest": "sha256:" + "f" * 64, "size": blob.stat().st_size, "locator": "materializations/v9/b.bin"}}],
            "reconstructability": {"lossless": True},
        }
        (d / "bad-blob.json").write_text(json.dumps(manifest, indent=2) + "\n")
        r = self.run_cli("check", self.ws)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("digest mismatch", r.stdout)

    def test_publish_and_activate_are_separate(self):
        self.init(); self.add_json_artifact(); self.assertEqual(self.run_cli("build-v9", self.ws).returncode, 0)
        self.assertEqual(self.run_cli("publish-v9", self.ws).returncode, 0)
        self.assertFalse((self.ws / "release/v9/channels/current.activation.json").exists())
        self.assertEqual(self.run_cli("activate-v9", self.ws, "--channel", "current").returncode, 0)
        act = json.loads((self.ws / "release/v9/channels/current.activation.json").read_text())
        self.assertEqual(act["sequence"], 1)
        self.assertEqual(self.run_cli("activate-v9", self.ws, "--channel", "current").returncode, 0)
        act2 = json.loads((self.ws / "release/v9/channels/current.activation.json").read_text())
        self.assertEqual(act2["sequence"], 2)
        self.assertIn("expected_previous", act2)

    def test_hash_manifest_and_pack_are_reproducible(self):
        self.init(); self.add_json_artifact(); self.assertEqual(self.run_cli("build-v9", self.ws).returncode, 0)
        self.assertEqual(self.run_cli("hash-manifest", self.ws).returncode, 0)
        first_manifest = (self.ws / "validation/manifest.sha256.json").read_bytes()
        self.assertEqual(self.run_cli("hash-manifest", self.ws).returncode, 0)
        self.assertEqual(first_manifest, (self.ws / "validation/manifest.sha256.json").read_bytes())
        a, b = self.tmp / "a.zip", self.tmp / "b.zip"
        self.assertEqual(self.run_cli("pack", self.ws, "--output", a).returncode, 0)
        self.assertEqual(self.run_cli("pack", self.ws, "--output", b).returncode, 0)
        self.assertEqual(a.read_bytes(), b.read_bytes())

    def test_migrate_v1_envelope(self):
        self.ws.mkdir()
        (self.ws / "canon/domain").mkdir(parents=True); (self.ws / "canon/domain/old.json").write_text("{}\n")
        (self.ws / "canon").mkdir(exist_ok=True); (self.ws / "sources").mkdir(); (self.ws / "projections/recipes").mkdir(parents=True)
        (self.ws / "kristal.workspace.json").write_text(json.dumps({
            "format": "kristal.authoring-workspace/1.0.0", "slug": "old", "title": "Old", "status": "building",
            "subject": {}, "semantic_ownership": {"owns": [], "does_not_own": []}, "native_model": {"kind": "json"},
            "derived_paths": ["derived", "projections/materialized"],
        }))
        (self.ws / "canon/state.index.json").write_text(json.dumps({"format":"kristal.authoring-state-index/1.0.0","canonical_artifacts":["canon/domain/old.json"],"derived_artifacts":[]}))
        (self.ws / "sources/source-catalog.json").write_text(json.dumps({"format":"kristal.source-catalog/1.0.0","sources":[]}))
        r = self.run_cli("migrate-v9", self.ws); self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        ws = json.loads((self.ws / "kristal.workspace.json").read_text()); self.assertEqual(ws["format"], "kristal.local-workspace/3.2.0")
        idx = json.loads((self.ws / "canon/state.index.json").read_text()); self.assertEqual(idx["format"], "kristal.authoring-state-index/2.0.0")
        self.assertIn("migration_note", idx["canonical_artifacts"][0])

    def test_migrate_v2_to_v3_preserves_state_index(self):
        self.init()
        ws_path = self.ws / "kristal.workspace.json"
        ws = json.loads(ws_path.read_text())
        ws["format"] = "kristal.authoring-workspace/2.0.0"
        ws["target"].pop("hosted_network_baseline", None)
        ws["release_policy"].pop("qualification_before_publication", None)
        ws["release_policy"].pop("exact_commit_publication", None)
        ws_path.write_text(json.dumps(ws, indent=2) + "\n")
        idx_before = (self.ws / "canon/state.index.json").read_bytes()
        r = self.run_cli("migrate-v10", self.ws)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        migrated = json.loads(ws_path.read_text())
        self.assertEqual(migrated["format"], "kristal.local-workspace/3.2.0")
        self.assertEqual(migrated["target"]["hosted_network_baseline"], "kristal.hosting/10.0")
        self.assertEqual(idx_before, (self.ws / "canon/state.index.json").read_bytes())

    def test_migrate_v3_to_v32_preserves_state_index(self):
        self.init()
        ws_path = self.ws / "kristal.workspace.json"
        ws = json.loads(ws_path.read_text())
        ws["format"] = "kristal.authoring-workspace/3.0.0"
        ws.pop("portable_ai", None)
        ws["derived_paths"] = [p for p in ws["derived_paths"] if p not in {"ai", "state"}]
        ws_path.write_text(json.dumps(ws, indent=2) + "\n")
        (self.ws / "AI_START_HERE.md").unlink(missing_ok=True)
        idx_before = (self.ws / "canon/state.index.json").read_bytes()
        r = self.run_cli("migrate-v10", self.ws)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        migrated = json.loads(ws_path.read_text())
        self.assertEqual(migrated["format"], "kristal.local-workspace/3.2.0")
        self.assertEqual(migrated["portable_ai"]["profile"], "kristal.portable-ai/1.0")
        self.assertFalse(migrated["portable_ai"]["enabled"])
        self.assertFalse((self.ws / "AI_START_HERE.md").exists())
        self.assertEqual(idx_before, (self.ws / "canon/state.index.json").read_bytes())

    def test_migrate_v31_preserves_existing_optional_ai_layer(self):
        self.init()
        self.add_json_artifact()
        self.assertEqual(self.run_cli("build-v9", self.ws, "--with-ai").returncode, 0)
        ws_path = self.ws / "kristal.workspace.json"
        ws = json.loads(ws_path.read_text())
        ws["format"] = "kristal.authoring-workspace/3.1.0"
        ws["portable_ai"].pop("enabled", None)
        ws_path.write_text(json.dumps(ws, indent=2) + "\n")
        idx_before = (self.ws / "canon/state.index.json").read_bytes()
        r = self.run_cli("migrate-v10", self.ws)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        migrated = json.loads(ws_path.read_text())
        self.assertEqual(migrated["format"], "kristal.local-workspace/3.2.0")
        self.assertTrue(migrated["portable_ai"]["enabled"])
        self.assertTrue((self.ws / "AI_START_HERE.md").is_file())
        self.assertEqual(idx_before, (self.ws / "canon/state.index.json").read_bytes())

    def test_configure_from_bootstrap_network(self):
        self.init()
        network = self.tmp / "network.toml"
        network.write_text("""[account]
owner = "example-owner"
kind = "user"

[framework]
repository = "example-owner/KristalV10"
ref = "0123456789abcdef0123456789abcdef01234567"

[hub]
repository = "kristal-hub"
visibility = "private"

[policy]
default_branch = "main"

[[collections]]
name = "kristal-public"
visibility = "public"
role = "collection"

[[collections]]
name = "kristal-private"
visibility = "private"
role = "collection"
""")
        r = self.run_cli("configure-from-network", self.ws, "--network", network, "--repository", "kristal-public")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        host = json.loads((self.ws / "hosting/github.json").read_text())
        self.assertEqual(host["repository"], "example-owner/kristal-public")
        self.assertEqual(host["framework"]["commit"], "0123456789abcdef0123456789abcdef01234567")

    def test_configure_github_and_export_hosted(self):
        self.init(); self.add_json_artifact()
        self.assertEqual(self.run_cli("build-v9", self.ws).returncode, 0)
        sha = "0123456789abcdef0123456789abcdef01234567"
        r = self.run_cli("configure-github", self.ws,
            "--repository", "example-owner/kristal-public",
            "--framework-repository", "example-owner/KristalV10",
            "--framework-sha", sha)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        host = json.loads((self.ws / "hosting/github.json").read_text())
        self.assertEqual(host["state_path"], "kristals/demo/state/state-snapshot.json")
        repo = self.tmp / "host-repo"
        (repo / ".git").mkdir(parents=True)
        (repo / ".kristal/bindings").mkdir(parents=True)
        (repo / ".kristal/node.json").write_text("{}\n")
        (repo / ".kristal/bindings/github.json").write_text("{}\n")
        r = self.run_cli("export-hosted", self.ws, "--repo-dir", repo)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        exported = repo / "kristals/demo/state/state-snapshot.json"
        self.assertEqual(exported.read_bytes(), (self.ws / "build/v9/state-snapshot.json").read_bytes())
        receipt = json.loads((self.ws / "build/v10/host-export.json").read_text())
        self.assertEqual(receipt["repository"], "example-owner/kristal-public")

    def test_hosting_metadata_does_not_change_state_commitment(self):
        self.init(); self.add_json_artifact()
        self.assertEqual(self.run_cli("build-v9", self.ws).returncode, 0)
        before = json.loads((self.ws / "build/v9/state-snapshot.json").read_text())["logical_commitment"]
        sha = "0123456789abcdef0123456789abcdef01234567"
        self.assertEqual(self.run_cli("configure-github", self.ws, "--repository", "a/public", "--framework-repository", "a/KristalV10", "--framework-sha", sha).returncode, 0)
        self.assertEqual(self.run_cli("build-v9", self.ws).returncode, 0)
        after = json.loads((self.ws / "build/v9/state-snapshot.json").read_text())["logical_commitment"]
        self.assertEqual(before, after)

    def test_utf8_reference_order_is_deterministic(self):
        def ref(aid, digit):
            return {"artifact_id": aid, "logical_contract":{"id":"x","version":"1"}, "logical_commitment":{"profile":"p","digest":"sha256:" + digit * 64}}
        a = {"members":[ref("urn:test:ä","1"), ref("urn:test:z","2")], "references":[]}
        b = {"members":list(reversed(a["members"])), "references":[]}
        self.assertEqual(kt.state_commitment(a), kt.state_commitment(b))

    def test_build_v9_does_not_generate_ai_by_default(self):
        self.init(); self.add_json_artifact()
        r = self.run_cli("build-v9", self.ws)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertFalse((self.ws / "AI_MANIFEST.json").exists())
        self.assertFalse((self.ws / "ai/CONTEXT.md").exists())
        self.assertTrue((self.ws / "build/v9/state-snapshot.json").is_file())

    def test_build_v9_with_ai_generates_optional_read_layer(self):
        self.init(); self.add_json_artifact()
        r = self.run_cli("build-v9", self.ws, "--with-ai")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        manifest = json.loads((self.ws / "AI_MANIFEST.json").read_text())
        state = json.loads((self.ws / "state/state-snapshot.json").read_text())
        built = json.loads((self.ws / "build/v9/state-snapshot.json").read_text())
        self.assertEqual(manifest["format"], "kristal.portable-ai/1.0")
        self.assertFalse(manifest["portable_reading"]["github_required"])
        self.assertFalse(manifest["portable_reading"]["network_required"])
        self.assertFalse(manifest["portable_reading"]["executable_tools_required"])
        self.assertEqual(state, built)
        self.assertEqual(manifest["state_logical_commitment"], built["logical_commitment"])
        self.assertEqual(self.run_cli("check-ai", self.ws).returncode, 0)

    def test_portable_ai_layer_is_deterministic(self):
        self.init(); self.add_json_artifact()
        self.assertEqual(self.run_cli("build-v9", self.ws).returncode, 0)
        self.assertEqual(self.run_cli("build-ai", self.ws).returncode, 0)
        first = {p.relative_to(self.ws).as_posix(): p.read_bytes() for p in [
            self.ws / "AI_MANIFEST.json", self.ws / "ai/CONTEXT.md", self.ws / "ai/INDEX.json",
            self.ws / "ai/COVERAGE.json", self.ws / "ai/RELATIONS.json", self.ws / "state/state-snapshot.json"
        ]}
        self.assertEqual(self.run_cli("build-ai", self.ws).returncode, 0)
        second = {rel: (self.ws / rel).read_bytes() for rel in first}
        self.assertEqual(first, second)

    def test_pack_ai_is_deterministic_and_excludes_github_tooling(self):
        self.init(); self.add_json_artifact()
        self.assertEqual(self.run_cli("build-v9", self.ws).returncode, 0)
        a, b = self.tmp / "portable-a.zip", self.tmp / "portable-b.zip"
        self.assertEqual(self.run_cli("pack-ai", self.ws, "--output", a).returncode, 0)
        self.assertEqual(self.run_cli("pack-ai", self.ws, "--output", b).returncode, 0)
        self.assertEqual(a.read_bytes(), b.read_bytes())
        with zipfile.ZipFile(a) as zf:
            names = set(zf.namelist())
        prefix = self.ws.name + "/"
        self.assertIn(prefix + "AI_START_HERE.md", names)
        self.assertIn(prefix + "AI_MANIFEST.json", names)
        self.assertIn(prefix + "state/state-snapshot.json", names)
        self.assertIn(prefix + "canon/state.index.json", names)
        self.assertFalse(any(n.startswith(prefix + "hosting/") for n in names))
        self.assertFalse(any(n.startswith(prefix + "tools/") for n in names))
        self.assertFalse(any(n.startswith(prefix + "build/") for n in names))


    def test_read_surface_is_exact_machine_projection_and_detects_staleness(self):
        self.init(); self.add_json_artifact()
        self.assertEqual(self.run_cli("build-v9", self.ws).returncode, 0)
        self.assertEqual(self.run_cli("build-ai", self.ws).returncode, 0)
        r = self.run_cli("read-surface", self.ws, "--compact", "--require-ready")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        surface = json.loads(r.stdout)
        self.assertEqual(surface["format"], "kristal.github-read-surface/1.0")
        self.assertEqual(surface["target_root"], "kristals/demo")
        self.assertTrue(surface["ready"])
        paths = {x["path"] for x in surface["files"]}
        self.assertIn("AI_START_HERE.md", paths)
        self.assertIn("AI_MANIFEST.json", paths)
        self.assertIn("ai/INDEX.json", paths)
        self.assertIn("canon/domain/core.json", paths)
        self.assertIn("state/state-snapshot.json", paths)
        self.assertTrue(surface["surface_digest"].startswith("sha256:"))
        # Read-surface readiness must fail if indexed bytes drift after build-ai.
        (self.ws / "canon/domain/core.json").write_text(json.dumps({"changed": True}) + "\n")
        r2 = self.run_cli("read-surface", self.ws, "--compact", "--require-ready")
        self.assertNotEqual(r2.returncode, 0)
        stale = json.loads(r2.stdout)
        self.assertFalse(stale["ready"])
        self.assertTrue(any("digest mismatch" in e for e in stale["errors"]))

    def test_portable_ai_indexes_materialization_manifest_and_local_blobs(self):
        self.init(); self.add_json_artifact()
        idx = json.loads((self.ws / "canon/state.index.json").read_text())
        ref = kt._canonical_ref_map(self.ws, idx)["urn:kristal:demo:core"]
        blobs = self.ws / "materializations/v9/blobs"; blobs.mkdir(parents=True)
        blob = blobs / "core.bin"; blob.write_bytes(b"reader-materialization")
        manifest = {
            "schema_version": "9.0", "artifact_type": "kristal_materialization_manifest",
            "materialization_id": "urn:kristal:materialization:demo:reader",
            "source": ref, "profile": "demo.materialization/reader/1",
            "segments": [{"segment_key": "all", "blob": {"media_type": "application/octet-stream", "digest": "sha256:" + kt.hash_file(blob), "size": blob.stat().st_size, "locator": "materializations/v9/blobs/core.bin"}}],
            "reconstructability": {"lossless": True},
        }
        src = self.tmp / "reader-mat.json"; src.write_text(json.dumps(manifest, indent=2) + "\n")
        self.assertEqual(self.run_cli("register-materialization", self.ws, "--manifest", src).returncode, 0)
        self.assertEqual(self.run_cli("build-v9", self.ws).returncode, 0)
        self.assertEqual(self.run_cli("build-ai", self.ws).returncode, 0)
        ai_index = json.loads((self.ws / "ai/INDEX.json").read_text())
        by_path = {x["path"]: x for x in ai_index["files"]}
        manifest_paths = [p for p, x in by_path.items() if x["role"] == "materialization_manifest"]
        self.assertEqual(len(manifest_paths), 1)
        self.assertNotIn("materializations/v9/blobs/core.bin", by_path)
        blob_rows = ai_index.get("materialization_blobs", [])
        self.assertEqual(len(blob_rows), 1)
        self.assertEqual(blob_rows[0]["path"], "materializations/v9/blobs/core.bin")
        self.assertEqual(blob_rows[0]["availability"], "workspace_local")
        self.assertEqual(blob_rows[0]["transport_class"], "materialization")
        coverage = json.loads((self.ws / "ai/COVERAGE.json").read_text())
        self.assertEqual(coverage["materialization_manifest_count"], 1)
        self.assertEqual(coverage["local_materialization_blob_count"], 1)
        self.assertEqual(coverage["external_materialization_locator_count"], 0)
        surface = json.loads(self.run_cli("read-surface", self.ws, "--compact").stdout)
        self.assertTrue(surface["ready"])
        surface_paths = {x["path"] for x in surface["files"]}
        self.assertNotIn("materializations/v9/blobs/core.bin", surface_paths)
        self.assertEqual(surface["materialization_object_count"], 1)
        self.assertEqual(surface["materialization_objects"][0]["path"], "materializations/v9/blobs/core.bin")
        a = self.tmp / "reader.zip"
        self.assertEqual(self.run_cli("pack-ai", self.ws, "--output", a).returncode, 0)
        with zipfile.ZipFile(a) as zf:
            names = set(zf.namelist())
        self.assertNotIn(self.ws.name + "/materializations/v9/blobs/core.bin", names)

    def test_external_references_are_explicit_not_silently_fetched(self):
        self.init(); self.add_json_artifact()
        digest = "sha256:" + "3" * 64
        self.assertEqual(self.run_cli("add-reference", self.ws, "--kind", "state", "--id", "urn:kristal:state:external", "--digest", digest).returncode, 0)
        self.assertEqual(self.run_cli("build-v9", self.ws).returncode, 0)
        self.assertEqual(self.run_cli("build-ai", self.ws).returncode, 0)
        coverage = json.loads((self.ws / "ai/COVERAGE.json").read_text())
        manifest = json.loads((self.ws / "AI_MANIFEST.json").read_text())
        self.assertEqual(coverage["semantic_closure"], "contains_pinned_external_references")
        self.assertEqual(coverage["external_reference_count"], 1)
        self.assertEqual(len(manifest["external_dependencies"]), 1)
        self.assertFalse(manifest["portable_reading"]["network_required"])

    def test_jcs_basics(self):
        self.assertEqual(kt.canonicalize({"b": 1, "a": 2}), '{"a":2,"b":1}')
        self.assertEqual(kt.canonicalize(1.0), '1')
        self.assertEqual(kt.canonicalize(0.000001), '0.000001')
        self.assertEqual(kt.canonicalize(1e-7), '1e-7')
        self.assertEqual(kt.canonicalize(-0.0), '0')

    def test_jcs_rfc8785_sample(self):
        obj = {
            "numbers": [333333333.33333329, 1E30, 4.50, 2e-3, 1e-27],
            "string": "€$\u000f\nA'B\"\\\"/",
            "literals": [None, True, False],
        }
        expected = "{\"literals\":[null,true,false],\"numbers\":[333333333.3333333,1e+30,4.5,0.002,1e-27],\"string\":\"€$\\u000f\\nA'B\\\"\\\\\\\"/\"}"
        self.assertEqual(kt.canonicalize(obj), expected)


if __name__ == "__main__":
    unittest.main()
