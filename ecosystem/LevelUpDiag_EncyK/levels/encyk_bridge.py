"""Check EncyK standalone Skope pull contract without downloading/importing anything."""
from pathlib import Path
from ._encyk_common import add, project_root, bounded_json, data_root, safe_children

def run(cfg, report):
    root=project_root(cfg)
    bridge=root/'00_system/integrations/skope_bridge.py'
    manifest=root/'MANIFEST.json'
    version=root/'VERSION'
    if not bridge.is_file() or not manifest.is_file() or not version.is_file():
        add(report,'encyk.bridge.contract','FAIL','EncyK standalone pull bridge or manifest is absent.')
        return
    try:
        m=bounded_json(manifest,128_000) or {}
        source=bridge.read_text(encoding='utf-8')
        v=version.read_text(encoding='utf-8').strip()
    except (OSError,ValueError) as exc:
        add(report,'encyk.bridge.contract','ERROR','Could not inspect pull contract.',{'error':str(exc)[:160]})
        return
    contract=m.get('contracts',{}).get('skope_pull')
    valid=(contract=='encyk.skope-pull/1.0' and v.startswith('0.14.') and
           'class SkopeClient:' in source and 'def pull(' in source and
           'def inspect_result(' in source and 'def list_jobs(' in source)
    add(report,'encyk.bridge.contract','PASS' if valid else 'FAIL',
        'Independent EncyK bridge and declared pull contract are aligned.',
        {'version':v,'contract':contract,'bridge_bytes':bridge.stat().st_size})
    forbidden=root/'00_system/tools/skope'
    add(report,'encyk.bridge.no_embedded_skope','FAIL' if forbidden.exists() else 'PASS',
        'No embedded Skope Python package remains in EncyK.',{'embedded_exists':forbidden.exists()})
    area=data_root(cfg)/'20_evidence/external-intake/skope'
    if not area.is_dir():
        add(report,'encyk.bridge.intake_area','WARN','No pulled Skope inventories recorded yet.',{'exists':False})
        return
    latest=[]
    for folder in safe_children(area,8):
        try:
            receipt=bounded_json(folder/'receipt.json',256_000)
            if receipt:
                latest.append({'job':folder.name,'contract':receipt.get('contract'),
                               'source_job_matches':receipt.get('source_job')==folder.name,
                               'source_kind':receipt.get('source_kind'),
                               'zip_present':(folder/'results.zip').is_file()})
        except (OSError,ValueError):
            latest.append({'job':folder.name,'receipt_error':True})
    good=all(x.get('contract')=='encyk.skope-pull/1.0' and
             x.get('source_job_matches') and x.get('zip_present') for x in latest)
    add(report,'encyk.bridge.intake_receipts','PASS' if latest and good else 'WARN',
        'Bounded, metadata-only inspection of existing noncanonical Skope imports.',
        {'recent_count':len(latest),'receipts':latest})
