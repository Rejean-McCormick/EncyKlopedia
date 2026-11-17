"""Exécuter SemantiK Architect sur des requêtes explicites, en espace privé.

Spek n'infère aucun fait, aucune requête ou aucun template. Les requêtes et le
plan de publication viennent de l'extérieur. L'exécution utilise l'interface
CLI officielle de SemantiK Architect; la sortie passe ensuite par le contrôle
strict de semantik_transfer avant de pouvoir être lue par les layouts Spek.

Aucun fichier du Kristal, d'Architect ou du dossier source n'est modifié.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any

from .core import ValidationError
from .slot_dialogue import from_files, compose_request, verify_result_shape
from .semantik_transfer import (
    TRANSFER_FORMAT, _ensure, _file, _read, _required_keys, transfer,
)


def _architect_root(root: Path, runtime_root: Path) -> tuple[Path, Path]:
    root = Path(root).expanduser().resolve(strict=True)
    runtime_root = Path(runtime_root).expanduser().resolve(strict=True)
    if not (root / 'src' / 'semantik_architect' / 'adapters' / 'inbound' / 'cli' / 'main.py').is_file():
        raise ValidationError('Dossier SemantiK Architect invalide : src/semantik_architect absent')
    if not runtime_root.is_dir() or runtime_root.is_symlink():
        raise ValidationError('Dossier RuntimeSet non admissible')
    return root, runtime_root


def _python_executable() -> str:
    """Windows .pyw may use pythonw.exe, which has no captured stdio."""
    path = Path(sys.executable)
    if os.name == 'nt' and path.name.lower() == 'pythonw.exe':
        console = path.with_name('python.exe')
        if console.is_file():
            return str(console)
    return sys.executable


def realize_mapping(
    article_path: Path,
    mapping_path: Path,
    architect_root: Path,
    runtime_root: Path,
    *,
    layouts: Path | None = None,
    state_snapshot: Path | None = None,
) -> dict[str, Any]:
    """Réalise seulement les requêtes déjà présentes dans une correspondance explicite.

    Tous les textes sont produits par SA et revalidés par le transfert existant.
    Aucun fallback texte brut, aucune sortie vers un dépôt public.
    """
    article_path = Path(article_path).expanduser().resolve(strict=True)
    mapping_path = Path(mapping_path).expanduser().resolve(strict=True)
    if article_path.is_symlink() or mapping_path.is_symlink():
        raise ValidationError('Source ou correspondance symbolique non autorisée')
    architect_root, runtime_root = _architect_root(architect_root, runtime_root)
    article, mapping = _read(article_path), _read(mapping_path)
    _ensure(mapping.get('format') == TRANSFER_FORMAT, 'format de correspondance incompatible')
    _ensure(set(mapping) <= {'format', 'language', 'bindings', 'note'}, 'champs inattendus')
    lang = mapping.get('language')
    _ensure(lang in ('fr', 'en', 'it'), 'langue inconnue')
    bindings = mapping.get('bindings')
    _ensure(isinstance(bindings, dict) and set(bindings) == _required_keys(article),
            'une requête explicite est requise pour chaque champ du template')
    _ensure(0 < len(bindings) <= 400, 'nombre de champs trop élevé')
    # Spek détermine la FORME à demander pour chaque champ de layout.
    # Les faits et obligations restent ceux de l'éditeur, inchangés.
    slot_plan = from_files(article_path, layouts or Path(__file__).resolve().parent.parent / 'layouts', lang)
    _ensure(set(slot_plan['fields']) == set(bindings), 'plan de formulation incomplet')

    # Valider tous les fichiers AVANT la première réalisation. Le modèle ne
    # fabrique jamais automatiquement les obligations ou les assertions.
    requests: dict[str, tuple[Path, Path, dict]] = {}
    used_paths = set()
    for key, pair in sorted(bindings.items()):
        _ensure(isinstance(pair, dict) and set(pair) == {'request', 'result'},
                f'{key} : chemins request/result exigés')
        request = _file(mapping_path.parent, pair['request'])
        result_rel = Path(pair['result'])
        _ensure(not result_rel.is_absolute() and '..' not in result_rel.parts
                and result_rel.suffix == '.json' and bool(result_rel.parts),
                f'{key} : chemin de résultat invalide')
        _ensure(pair['request'] not in used_paths and pair['result'] not in used_paths,
                f'{key} : chemin réutilisé')
        used_paths.update((pair['request'], pair['result']))
        obj = _read(request)
        _ensure(obj.get('schema_version') == '1.0'
                and isinstance(obj.get('obligations'), list) and bool(obj['obligations'])
                and isinstance(obj.get('semantic_graph'), dict),
                f'{key} : requête sémantique complète requise')
        _ensure(isinstance(obj.get('context'), dict)
                and obj['context'].get('target_language') == lang,
                f'{key} : langue de requête différente')
        # Bloquer les conflits de mode communicatif avant toute exécution.
        prepared_request = compose_request(obj, slot_plan['fields'][key], language=lang)
        requests[key] = (request, result_rel, prepared_request)

    private_root = Path(tempfile.mkdtemp(prefix='spek-semantik-realisation-privee-'))
    bundle = private_root / 'entrees'
    bundle.mkdir()
    runtime_env = os.environ.copy()
    src = str(architect_root / 'src')
    runtime_env['PYTHONPATH'] = src + (os.pathsep + runtime_env['PYTHONPATH'] if runtime_env.get('PYTHONPATH') else '')
    safe_mapping = {'format': TRANSFER_FORMAT, 'language': lang, 'bindings': bindings}
    (bundle / 'mapping.json').write_text(json.dumps(safe_mapping, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    for key, (source, result_rel, prepared_request) in sorted(requests.items()):
        request_rel = Path(bindings[key]['request'])
        target_request = bundle / request_rel
        target_result = bundle / result_rel
        for target in (target_request, target_result):
            _ensure(target.resolve().is_relative_to(bundle.resolve()), 'sortie hors espace privé')
            target.parent.mkdir(parents=True, exist_ok=True)
        # Espace temporaire privé : garder intacte la requête d'origine.
        # Le texte sera réalisé à partir de la requête CONTRAINTE par Spek.
        target_request.write_text(json.dumps(prepared_request, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        cmd = [_python_executable(), '-m', 'semantik_architect.adapters.inbound.cli.main',
               '--runtime-root', str(runtime_root), 'render', str(target_request)]
        try:
            process = subprocess.run(cmd, cwd=architect_root, env=runtime_env, capture_output=True,
                                     text=True, encoding='utf-8', timeout=45, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ValidationError(f'SemantiK indisponible pour « {key} » : {exc}') from exc
        if process.returncode:
            # No raw arbitrary stderr/request data in a GUI error; preserve
            # technical details only in the application's diagnostics elsewhere.
            raise ValidationError(
                f'SemantiK ne peut pas réaliser « {key} ». Vérifie le RuntimeSet GF/PGF, '
                'le profil et les requêtes explicites. Aucune phrase de remplacement créée.'
            )
        try:
            result = json.loads(process.stdout)
        except (ValueError, TypeError) as exc:
            raise ValidationError(f'SemantiK a retourné un résultat non JSON pour « {key} »') from exc
        _ensure(isinstance(result, dict) and result.get('schema_version') == '1.0',
                f'{key} : résultat SemantiK invalide')
        verify_result_shape(result, slot_plan['fields'][key], request=prepared_request)
        # The existing verified transfer checks obligation coverage, language,
        # RuntimeSet, source references and deterministic result identity.
        target_result.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    verified = transfer(article_path, bundle / 'mapping.json', private_root / 'resultat',
                        layouts=layouts, state_snapshot=state_snapshot)
    return {**verified, 'source': 'semantik_architect_runtime', 'private_work_dir': str(private_root)}


def main(argv: list[str] | None = None) -> int:
    """Operator CLI. All sources explicit, no automatic selections."""
    import argparse
    parser = argparse.ArgumentParser(description='Réaliser un article Spek via SemantiK Architect (privé)')
    parser.add_argument('--article', required=True, type=Path)
    parser.add_argument('--mapping', required=True, type=Path)
    parser.add_argument('--architect', required=True, type=Path)
    parser.add_argument('--runtime-root', required=True, type=Path)
    parser.add_argument('--layouts', type=Path)
    parser.add_argument('--snapshot', type=Path)
    args = parser.parse_args(argv)
    try:
        result = realize_mapping(args.article, args.mapping, args.architect,
                                 args.runtime_root, layouts=args.layouts,
                                 state_snapshot=args.snapshot)
    except (ValidationError, ValueError, OSError) as exc:
        parser.exit(2, 'Échec : ' + str(exc) + '\n')
    print(json.dumps({'status': result['status'], 'realizations': str(result['realizations']),
                      'language': result['language'], 'note': 'APERÇU PRIVÉ, NON PUBLIABLE'},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
