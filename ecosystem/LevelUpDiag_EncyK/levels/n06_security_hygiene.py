from __future__ import annotations
import re
from pathlib import Path
from levelupdiag_core.scanner import iter_files
from levelupdiag_core.util import bounded_text

PATTERNS = [
  ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
  ("github-token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b")),
  ("github-fine-grained-token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{30,}\b")),
  ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
  ("generic-secret-assignment", re.compile(r"(?i)\b(?:api[_-]?key|secret|access[_-]?token)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{20,}")),
]
SENSITIVE_NAMES={".env","id_rsa","id_dsa","id_ecdsa","id_ed25519"}

def run(cfg, report):
    if not cfg.get("security",{}).get("enabled",True):
        report.add("security.hygiene.enabled", "SKIP", "security_hygiene", "Security hygiene scan is disabled by configuration."); return
    target=Path(cfg["_target_root"]); scan=cfg.get("scan",{}); max_files=int(scan.get("max_security_files",4000)); max_bytes=min(int(scan.get("max_file_bytes",1048576)),1048576)
    extra=cfg.get("security",{}).get("additional_excluded_globs",[]); hits=[]; names=[]; scanned=0
    custom=[]
    for i, pat in enumerate(cfg.get("security",{}).get("additional_patterns",[])):
        try: custom.append((f"custom-{i+1}",re.compile(pat)))
        except re.error as e: report.add(f"security.pattern.custom_{i+1}","CONFIG_ERROR","security_hygiene","Invalid configured security regex.",evidence=str(e)); return
    patterns=PATTERNS+custom
    for p, rel in iter_files(target,cfg,max_files=max_files,extra_globs=extra):
        if p.is_symlink():
            continue
        scanned+=1
        if p.name in SENSITIVE_NAMES: names.append(rel)
        text=bounded_text(p,max_bytes)
        if text is None: continue
        for pid, rx in patterns:
            m=rx.search(text)
            if m:
                line=text.count("\n",0,m.start())+1
                hits.append({"pattern":pid,"path":rel,"line":line})
                break
    report.add("security.sensitive_filenames.review", "WARN" if names else "PASS", "security_hygiene", "Potentially sensitive filenames were found and should be reviewed." if names else "No high-risk sensitive filenames were found in the bounded scan.", evidence=names[:100] if names else None)
    report.add("security.secret_patterns.review", "WARN" if hits else "PASS", "security_hygiene", "Potential secret material matched conservative patterns; values are intentionally not copied into evidence." if hits else "No configured secret pattern matched in the bounded scan.", evidence=hits[:100] if hits else None, recommendation="Rotate exposed credentials and remove them from history if any match is genuine." if hits else None)
    if scanned>=max_files: report.add("security.scan.truncated","WARN","security_hygiene","Security hygiene scan reached its file limit.",recommendation="Raise scan.max_security_files if broader evidence is required.")
    report.metrics.update({"files_scanned":scanned,"potential_secret_hits":len(hits),"sensitive_filenames":len(names)})
