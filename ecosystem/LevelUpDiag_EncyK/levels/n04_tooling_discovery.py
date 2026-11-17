from __future__ import annotations
import shutil
from pathlib import Path
from levelupdiag_core.scanner import iter_files

SURFACES = {
  "pyproject.toml": ["python"], "requirements.txt":["python"], "package.json":["node"],
  "Cargo.toml":["cargo"], "go.mod":["go"], "pom.xml":["java","mvn"],
  "build.gradle":["java"], "build.gradle.kts":["java"], "composer.json":["php"],
  "Gemfile":["ruby"], "mix.exs":["elixir"], "Makefile":["make"], "CMakeLists.txt":["cmake"]
}
LOCK_NAMES = {"uv.lock","poetry.lock","Pipfile.lock","package-lock.json","pnpm-lock.yaml","yarn.lock","bun.lockb","Cargo.lock","go.sum","composer.lock","Gemfile.lock"}
CI_PARTS = {".github/workflows",".gitlab-ci.yml","azure-pipelines.yml","Jenkinsfile",".circleci"}

def run(cfg, report):
    target=Path(cfg["_target_root"]); found=[]; candidates=set(); locks=[]; automation=[]
    for p, rel in iter_files(target,cfg,max_files=10000):
        name=p.name
        if name in SURFACES:
            found.append(rel); candidates.update(SURFACES[name])
        if name in LOCK_NAMES: locks.append(rel)
        if any(rel==x or rel.startswith(x.rstrip("/")+"/") for x in CI_PARTS): automation.append(rel)
    availability={tool:bool(shutil.which(tool)) for tool in sorted(candidates)}
    report.add("tooling.surfaces.discovered", "PASS", "tooling", "Project tooling surfaces were discovered without executing them.", evidence={"manifests":found,"lock_files":locks,"automation_sample":automation[:50]})
    missing=[x for x,ok in availability.items() if not ok]
    if missing:
        report.add("tooling.candidates.available", "WARN", "tooling", "Some tools suggested by repository manifests are not available on PATH; they are not assumed to be required.", evidence={"availability":availability})
    else:
        report.add("tooling.candidates.available", "PASS", "tooling", "All locally inferred candidate tools are available, or no tool requirement was inferred.", evidence={"availability":availability})
    required=cfg.get("toolchain",{}).get("required",[])
    req_missing=[x for x in required if not shutil.which(x)]
    report.add("tooling.required.available", "BLOCKED" if req_missing else "PASS", "tooling", "Configured required tools are available." if not req_missing else "Configured required tools are missing.", evidence=req_missing or required)
    report.metrics.update({"candidate_tools":availability,"manifests":found,"lock_files":locks})
