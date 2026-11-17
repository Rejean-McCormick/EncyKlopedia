from __future__ import annotations

import copy
import os
from pathlib import Path
from .util import read_json



class ConfigError(RuntimeError):
    pass


def _merge(base, overlay):
    out = copy.deepcopy(base)
    for k, v in overlay.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def _load_encyk_config(tool_root: Path, target_override=None):
    """External EncyK repository; never place runtime reports in the target."""
    tool_root = Path(tool_root).resolve()
    cfg = read_json(tool_root / 'levelupdiag.config.json')
    local = tool_root / 'levelupdiag.config.local.json'
    if local.exists():
        cfg = _merge(cfg, read_json(local))
    if cfg.get('schema') != 'levelupdiag.config.v2':
        raise ConfigError('Unsupported EncyK profile schema')
    raw = target_override or cfg.get('target_repo_root')
    if not raw or str(raw).lower() == 'auto':
        raise ConfigError('A separate EncyK repository must be provided with --target')
    p = Path(raw).expanduser()
    target = (p if p.is_absolute() else tool_root / p).resolve(strict=False)
    if not target.is_dir() or not all((target / path).is_file() for path in ('MANIFEST.json', 'VERSION', '00_system/integrations/skope_bridge.py')):
        raise ConfigError('EncyK standalone target not found (MANIFEST.json, VERSION, Skope bridge required): ' + str(target))
    if target == tool_root or tool_root.is_relative_to(target) or target.is_relative_to(tool_root):
        raise ConfigError('LevelUpDiag and EncyK must be separate non-nested repositories')
    ctl = Path(cfg.get('control_dir', '.levelupdiag/encyk'))
    if ctl.is_absolute() or '..' in ctl.parts or not ctl.parts or ctl.parts[0] != '.levelupdiag':
        raise ConfigError('Diagnostic reports must remain inside LevelUpDiag/.levelupdiag')
    control = (tool_root / ctl).resolve(strict=False)
    if not control.is_relative_to(tool_root / '.levelupdiag'):
        raise ConfigError('Report directory escapes LevelUpDiag')
    if cfg.get('execution', {}).get('allow_target_mutation', False):
        raise ConfigError('EncyK diagnostics cannot mutate the target')
    if cfg.get('execution', {}).get('allow_network', False):
        raise ConfigError('EncyK diagnostics cannot enable general network access')
    cfg['_tool_root'] = str(tool_root)
    cfg['_target_root'] = str(target)
    cfg['_control_root'] = str(control)
    return cfg


def load_config(tool_root: Path, target_override=None):
    """EncyK-only diagnostics; no alternative applications or profiles."""
    return _load_encyk_config(tool_root, target_override)
