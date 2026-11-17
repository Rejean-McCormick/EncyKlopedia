from __future__ import annotations
import os, platform, sys
from pathlib import Path
from levelupdiag_core.commands import which, run_command
from levelupdiag_core.vcs import git_info


def run(cfg, report):
    target = Path(cfg["_target_root"]); tool = Path(cfg["_tool_root"]); control = Path(cfg["_control_root"])
    report.add("target.root.exists", "PASS" if target.is_dir() else "CONFIG_ERROR", "target", "Target repository root is available.", path=str(target))
    report.add("target.layout.standalone", "PASS", "target", "EncyK and LevelUpDiag are separate repositories; reports remain in LevelUpDiag.", evidence={"tool_root":str(tool),"target_root":str(target),"control_root":str(control)})
    report.add("runtime.platform.detected", "PASS", "environment", "Runtime platform detected.", evidence={"system":platform.system(),"release":platform.release(),"python":sys.version.split()[0]})
    gi = git_info(target)
    if gi.get("repository"):
        report.add("target.vcs.git.detected", "PASS", "vcs", "Git repository detected.", evidence={"head":gi.get("head"),"branch":gi.get("branch"),"tracked_dirty":bool(gi.get("tracked_status"))})
        try:
            rel_control = control.relative_to(target).as_posix()
            ignored = run_command(["git", "check-ignore", "-q", "--", rel_control], cwd=target, timeout_seconds=10, capture_limit_kb=16)
            report.add("target.control_dir.ignored", "PASS" if ignored["exit_code"] == 0 else "WARN", "vcs",
                       "Generated LevelUpDiag evidence is ignored by Git." if ignored["exit_code"] == 0 else "Generated LevelUpDiag evidence is not ignored by Git.",
                       evidence={"control_dir":rel_control}, recommendation=None if ignored["exit_code"] == 0 else f"Add {rel_control}/ to the target repository ignore rules.")
        except ValueError:
            pass
    else:
        report.add("target.vcs.detected", "WARN", "vcs", "No Git repository was detected; VCS protection will be limited.", evidence={"git_available":gi.get("available")})
    report.metrics.update({"cwd":os.getcwd(),"control_root":str(control),"git":gi})
