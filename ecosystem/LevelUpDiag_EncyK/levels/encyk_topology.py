"""EncyK code on C:, data on D:, without accessing large files."""
from pathlib import Path
from ._encyk_common import data_root, project_root,add

def run(cfg,report):
    repo=project_root(cfg);root=data_root(cfg)
    code=repo/'00_system/tools/skope'
    add(report,'encyk.code.skope_decoupled','FAIL' if code.exists() else 'PASS',
        'Skope Python backend must NOT exist inside EncyK 0.14.',{'integrated_skope_exists':code.exists()})
    launcher=repo/'Lancer_Skope.pyw'
    add(report,'encyk.code.skope_launcher_removed','FAIL' if launcher.exists() else 'PASS',
        'Legacy Skope launcher is no longer part of EncyK.', {'obsolete_launcher_exists':launcher.exists()})
    bridge=repo/'00_system/integrations/skope_bridge.py'
    add(report,'encyk.code.skope_pull_bridge','PASS' if bridge.is_file() else 'FAIL',
        'EncyK consumes standalone Skope results through an independent pull bridge.', {'bridge_exists':bridge.is_file()})
    add(report,'encyk.data.root','PASS' if root.is_dir() else 'BLOCKED',
        'EncyK external data volume is accessible.',{'data_root':str(root),'exists':root.is_dir()},
        'Check D:\\EncyKlopedia and its volume mount; do not copy datasets to C:' if not root.is_dir() else None)
    for dirname in ('10_sources','20_evidence','30_working','40_kristal','50_mediatheque','90_runtime'):
        d=root/dirname
        add(report,'encyk.data.area.'+dirname,'PASS' if d.is_dir() else 'WARN',
            f'Data area {dirname} is available.' if d.is_dir() else f'Data area {dirname} is missing.',
            {'exists':d.is_dir()},None if d.is_dir() else 'Review data layout; never create or delete areas automatically')
    if root.exists():
        try:
            if repo.resolve()==root.resolve():
                add(report,'encyk.data.separation','FAIL','Code and data roots resolve to the same directory.')
            else:add(report,'encyk.data.separation','PASS','Source and data roots are distinct.')
        except OSError: pass
    for rel in ('20_evidence','30_working','90_runtime'):
        link=repo/rel
        # Report facts, do not assume a junction is an error if direct D: is accessible.
        add(report,'encyk.junction.'+rel,'PASS' if link.exists() else 'WARN',
            f'{rel} visible under source repository.' if link.exists() else f'{rel} is not visible under source repository.',
            {'visible':link.exists(),'is_symlink':link.is_symlink()},
            'EncyK and Skope can access D: independently; verify junctions with the explicit config script.' if not link.exists() else None)
