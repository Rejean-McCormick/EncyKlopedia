"""Check declared Kristal target only, without loading payloads or changing canon."""
from pathlib import Path
from ._encyk_common import add,bounded_json

def run(cfg,report):
    folder=Path(cfg.get('encyk',{}).get('kristal_root',''))
    manifest=folder/'kristal.workspace.json'
    try:j=bounded_json(manifest,512_000)
    except (OSError,ValueError) as exc:
        add(report,'encyk.kristal.workspace','FAIL','Target workspace could not be parsed.',{'error':str(exc)[:200]});return
    if not isinstance(j,dict):
        add(report,'encyk.kristal.workspace','WARN','Target Kristal workspace not found.');return
    state=j.get('target') or {}
    add(report,'encyk.kristal.workspace','PASS' if str(j.get('format','')).startswith('kristal.local-workspace/') else 'FAIL',
        'Kristal workspace metadata inspected without modifying the canon.',{'slug':j.get('slug'),'state_ref':j.get('state_ref'),
            'state_architecture':state.get('state_architecture')})
    for name,rel in [('canonical','canon/state.index.json'),('discovery','kristal.discovery.json')]:
        p=folder/rel
        add(report,'encyk.kristal.'+name,'PASS' if p.is_file() else 'WARN',
            f'Kristal {name} metadata exists.' if p.is_file() else f'Kristal {name} metadata is absent.',
            {'exists':p.is_file()})
