from __future__ import annotations
from collections import Counter
from pathlib import Path
from levelupdiag_core.scanner import iter_files
from levelupdiag_core.util import write_json

MANIFESTS = {
  "pyproject.toml":"python-project", "requirements.txt":"python-requirements", "package.json":"node-project",
  "Cargo.toml":"rust-project", "go.mod":"go-project", "pom.xml":"maven-project", "build.gradle":"gradle-project",
  "build.gradle.kts":"gradle-project", "composer.json":"php-project", "Gemfile":"ruby-project", "mix.exs":"elixir-project",
  "*.sln":"dotnet-solution", "*.csproj":"dotnet-project", "Makefile":"make", "CMakeLists.txt":"cmake"
}
DOCS = {"README.md","README.rst","README.txt","CONTRIBUTING.md","CHANGELOG.md","LICENSE","LICENSE.md","SECURITY.md"}

def match_manifest(rel):
    name = Path(rel).name
    for pat, kind in MANIFESTS.items():
        if pat.startswith("*.") and name.endswith(pat[1:]): return kind
        if name == pat: return kind
    return None


def run(cfg, report):
    target = Path(cfg["_target_root"]); ext = Counter(); manifests=[]; docs=[]; total_bytes=0; count=0
    for p, rel in iter_files(target, cfg):
        count += 1
        try: total_bytes += p.lstat().st_size
        except OSError: pass
        suffix = p.suffix.lower() or "<none>"; ext[suffix]+=1
        kind = match_manifest(rel)
        if kind: manifests.append({"path":rel,"kind":kind})
        if p.name in DOCS: docs.append(rel)
    inv = {"file_count":count,"bounded_bytes":total_bytes,"top_extensions":ext.most_common(30),"manifests":manifests,"documentation":docs}
    out = Path(cfg["_control_root"]) / "inventory" / f"{report.run_id}.json"
    write_json(out, inv); report.artifact("inventory", out, "Bounded repository inventory")
    report.add("repository.inventory.completed", "PASS", "inventory", "Bounded repository inventory completed.", evidence={"files":count,"manifests":len(manifests),"docs":len(docs)})
    if count >= int(cfg.get("scan",{}).get("max_files",20000)):
        report.add("repository.inventory.truncated", "WARN", "inventory", "Inventory reached the configured file limit.", recommendation="Raise scan.max_files if full inventory evidence is required.")
    report.metrics.update(inv)
