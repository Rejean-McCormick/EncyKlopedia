from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def section(title: str) -> None:
    print(f"\n=== {title} ===", flush=True)


def run(*args: str) -> None:
    cmd = [sys.executable, *args]
    print("+", " ".join(cmd), flush=True)
    completed = subprocess.run(cmd, cwd=ROOT)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def validate_json() -> None:
    roots = [
        ROOT / "MANIFEST.json",
        ROOT / "00_system",
        ROOT / "10_sources",
        ROOT / "20_evidence",
    ]
    files: list[Path] = []
    for base in roots:
        if base.is_file():
            files.append(base)
        elif base.is_dir():
            files.extend(base.rglob("*.json"))

    failures: list[str] = []
    for path in sorted(set(files)):
        try:
            json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception as exc:  # report every malformed tracked JSON in one pass
            failures.append(f"{path.relative_to(ROOT)}: {exc}")

    if failures:
        print("Malformed JSON:")
        for failure in failures:
            print(" -", failure)
        raise SystemExit(1)
    print(f"JSON parse: PASS ({len(files)} files)")


def validate_python_syntax() -> None:
    files = list((ROOT / "00_system").rglob("*.py"))
    files += list((ROOT / "00_system").rglob("*.pyw"))
    files += list(ROOT.glob("*.py"))
    files += list(ROOT.glob("*.pyw"))

    failures: list[str] = []
    for path in sorted(set(files)):
        try:
            source = path.read_text(encoding="utf-8-sig")
            compile(source, str(path), "exec")
        except Exception as exc:
            failures.append(f"{path.relative_to(ROOT)}: {exc}")

    if failures:
        print("Python syntax failures:")
        for failure in failures:
            print(" -", failure)
        raise SystemExit(1)
    print(f"Python syntax: PASS ({len(files)} files)")


def main() -> int:
    section("Repository architecture")
    run("00_system/tools/validate_repo.py")

    section("JSON integrity")
    validate_json()

    section("Python syntax")
    validate_python_syntax()

    section("Scope Builder and Wikidata Manager tests")
    run(
        "-m",
        "pytest",
        "-q",
        "00_system/tools/scope-builder/tests/test_scope_pipeline.py",
        "00_system/tools/wikidata-manager/tests/test_core.py",
    )

    section("Result")
    print("EncyK Fast CI: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
