from __future__ import annotations
import os
from pathlib import Path
from levelupdiag_core.scanner import iter_files
from levelupdiag_core.util import bounded_text

MARKERS = ("<<<<<<< ", "=======", ">>>>>>> ")

def run(cfg, report):
    target = Path(cfg["_target_root"]); scan=cfg.get("scan",{}); max_bytes=int(scan.get("max_file_bytes",1048576)); large=int(scan.get("large_file_bytes",10485760))
    broken=[]; conflicts=[]; huge=[]; names=[]
    for p, rel in iter_files(target, cfg):
        try:
            if p.is_symlink():
                if not p.exists(): broken.append(rel)
                continue
            size=p.lstat().st_size
        except OSError: continue
        if size > large: huge.append({"path":rel,"bytes":size})
        if any(ord(c)<32 for c in p.name): names.append(rel)
        text=bounded_text(p,max_bytes)
        if text is not None and all(m in text for m in MARKERS):
            conflicts.append(rel)
    report.add("repository.symlinks.valid", "WARN" if broken else "PASS", "hygiene", "Broken symbolic links detected." if broken else "No broken symbolic links detected in the bounded scan.", evidence=broken[:100] if broken else None)
    report.add("repository.merge_markers.absent", "WARN" if conflicts else "PASS", "hygiene", "Possible unresolved merge markers detected." if conflicts else "No unresolved merge-marker pattern detected in bounded text files.", evidence=conflicts[:100] if conflicts else None)
    report.add("repository.large_files.review", "WARN" if huge else "PASS", "hygiene", "Large repository files should be reviewed." if huge else "No files exceeded the configured large-file threshold.", evidence=huge[:100] if huge else None)
    if names: report.add("repository.path_names.portable", "WARN", "hygiene", "Control characters were found in file names.", evidence=names[:100])
    report.metrics.update({"broken_symlinks":len(broken),"possible_conflicts":len(conflicts),"large_files":len(huge)})
