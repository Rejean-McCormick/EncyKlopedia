"""Correlate local fast-access check against Skope's live preflight (repeated safely)."""
from ._encyk_common import add
from . import encyk_reader,encyk_skope

def compare(local,remote):
    p=remote.get('preflight') or {}
    source=p.get('source') or p.get('source_check') or {}
    # Support actual response shapes without inferring a backend where none was returned.
    if 'fast_backend' not in source and 'fast_backend' in p:source=p
    local_ready=local.get('random_access_ready')
    remote_backend=source.get('fast_backend')
    remote_ready=source.get('random_access_ready')
    if not remote.get('up'):
        return 'BLOCKED','No live Skope process could be checked.'
    if not p:
        return 'PARTIAL','Live Skope extraction preflight is unavailable.'
    if remote_backend is None or remote_ready is None:
        return 'PARTIAL','Preflight response does not expose reader backend details.'
    if local_ready and remote_ready is False:
        return 'FAIL','CONFIRMED PARITY MISMATCH: local random access works but Skope server reports unavailable.'
    if local_ready and remote_ready:
        return 'PASS','Local reader and Skope server both report random-access capability.'
    if not local_ready and remote_ready:
        return 'FAIL','Reverse mismatch: Skope reports reader ready but local check does not.'
    return 'BLOCKED','Both environments report random access unavailable; review local import and sidecars.'

def run(cfg,report):
    try:local=encyk_reader.collect(cfg)
    except Exception as ex:
        add(report,'encyk.reader.parity.local','ERROR','Local parity probe failed.',{'error':type(ex).__name__+': '+str(ex)[:250]});return
    try:remote=encyk_skope.collect(cfg,True)
    except Exception as ex:
        add(report,'encyk.reader.parity.remote','ERROR','Server parity probe failed.',{'error':type(ex).__name__+': '+str(ex)[:250]});return
    verdict,text=compare(local,remote)
    preflight=remote.get('preflight') or {}
    source=preflight.get('source') or preflight.get('source_check') or {}
    detail={'local_python':local.get('python'),'local_reader_importable':local.get('imported_reader'),
           'local_fastio_cached':local.get('cached_indexed_bzip2'),
           'local_backend':local.get('backend'),'local_random_access':local.get('random_access_ready'),
           'server_api_up':remote.get('up'),'server_process':remote.get('pid'),
           'server_backend':source.get('fast_backend'), 'server_random_access':source.get('random_access_ready'),
           'server_reader_probe':source.get('reader_probe'),'preflight_error':remote.get('preflight_error'),
           'server_python':(remote.get('process_reader') or {}).get('python_executable'),
           'server_reader_importable':(remote.get('process_reader') or {}).get('reader_importable'),
           'server_reader_cached':(remote.get('process_reader') or {}).get('fastio_reader_cached'),
           'server_scope_common_file':(remote.get('process_reader') or {}).get('scope_common_file')}
    add(report,'encyk.reader.parity.live',verdict,text,detail,
        'Compare independent EncyK and Skope readers by capability and interpreter; they are not the same Python package. Never rebuild the dump or sidecars.' if verdict!='PASS' else None)
