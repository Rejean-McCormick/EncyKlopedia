"""Fail-closed, offline transfer of explicit SemantiK Architect communication results.

This adapter does not create requests, select assertions/templates, certify RuntimeSets,
or publish. A result+request pair is supplied for EVERY Spek realization key.
The source/artifacts remain read-only and output is a *new private directory*.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import shutil
from pathlib import Path
from typing import Any

from .core import ValidationError, compile_inputs, read_json, SEMANTIC_FORMAT

TRANSFER_FORMAT = 'spek.semantik-transfer/1.0'
SHA = re.compile(r'^sha256:[a-f0-9]{64}$')


def _ensure(ok: Any, message: str) -> None:
    if not ok:
        raise ValidationError('Transfert SemantiK : ' + message)


def _file(base: Path, rel: str) -> Path:
    _ensure(isinstance(rel, str) and bool(rel.strip()), 'chemin requis')
    path = Path(rel)
    _ensure(not path.is_absolute() and '..' not in path.parts and path.suffix == '.json', 'chemin relatif JSON requis')
    root = base.resolve()
    target = base / path
    _ensure(target.resolve().is_relative_to(root), 'fichier hors du dossier de transfert')
    walk = base
    for part in path.parts:
        walk = walk / part
        _ensure(not walk.is_symlink(), 'lien symbolique interdit')
    _ensure(target.is_file() and target.stat().st_size <= 5_000_000, 'JSON absent ou trop volumineux : ' + rel)
    return target


def _read(path: Path) -> dict[str, Any]:
    try:
        return read_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise ValidationError('Transfert SemantiK : JSON invalide ' + str(path)) from exc


def _hash_file(path: Path) -> str:
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def _required_keys(article: dict) -> set[str]:
    _ensure(article.get('format') == SEMANTIC_FORMAT, 'format article.json incompatible')
    meta = article.get('article')
    _ensure(isinstance(meta, dict), 'objet article absent')
    keys: set[str] = set()
    for field in ('title_key', 'subtitle_key', 'abstract_key'):
        key = meta.get(field)
        _ensure(isinstance(key, str) and key.strip(), 'clé article manquante : ' + field)
        keys.add(key)
    units = {}
    for item in article.get('units', []):
        _ensure(isinstance(item, dict) and isinstance(item.get('id'), str) and isinstance(item.get('realization_key'), str), 'unité invalide')
        _ensure(item['id'] not in units, 'unité dupliquée')
        units[item['id']] = item['realization_key']
    for item in article.get('evidence', []):
        _ensure(isinstance(item, dict) and isinstance(item.get('id'), str) and isinstance(item.get('realization_key'), str), 'preuve invalide')
        _ensure(item['id'] not in units, 'référence unité/preuve dupliquée')
        units[item['id']] = item['realization_key']
    _ensure(isinstance(article.get('sections'), list) and bool(article['sections']), 'aucune section')
    for section in article['sections']:
        _ensure(isinstance(section, dict) and isinstance(section.get('heading_key'), str), 'titre de section manquant')
        keys.add(section['heading_key'])
        slots = section.get('slots')
        _ensure(isinstance(slots, dict), 'emplacements de section manquants')
        for refs in slots.values():
            refs = [refs] if isinstance(refs, str) else refs
            _ensure(isinstance(refs, list), 'référence d’emplacement invalide')
            for ref in refs:
                _ensure(ref in units, 'référence de section inconnue : ' + str(ref))
                keys.add(units[ref])
    return keys


def _from_blocks(blocks: list) -> tuple[str, dict[str, set[str]]]:
    texts: list[str] = []
    by_obligation: dict[str, set[str]] = {}
    seen = set()
    for b in blocks:
        _ensure(isinstance(b, dict) and isinstance(b.get('block_id'), str), 'bloc SemantiK invalide')
        bid = b['block_id']
        _ensure(bid not in seen, 'bloc SemantiK dupliqué')
        seen.add(bid)
        kind = b.get('kind')
        if kind == 'list':
            items = b.get('items')
            _ensure(isinstance(items, list) and bool(items), 'liste SemantiK vide')
            for item in items:
                _ensure(isinstance(item, dict) and isinstance(item.get('text'), str), 'item liste invalide')
                texts.append('- ' + item['text'])
        elif kind == 'label_value':
            _ensure(isinstance(b.get('label'), str) and isinstance(b.get('value'), str), 'label_value invalide')
            texts.append(b['label'] + ': ' + b['value'])
        else:
            _ensure(kind in {'utterance', 'question', 'notice', 'heading'} and isinstance(b.get('text'), str), 'type de bloc inconnu')
            if b['text']:
                texts.append(b['text'])
        oids = b.get('obligation_ids')
        _ensure(isinstance(oids, list) and all(isinstance(x, str) for x in oids), 'obligations du bloc invalides')
        for oid in oids:
            by_obligation.setdefault(oid, set()).add(bid)
    return '\n'.join(texts), by_obligation


def _source_refs(request: dict) -> list[str]:
    by_id = {}
    graph = request.get('semantic_graph')
    _ensure(isinstance(graph, dict), 'graphe de requête absent')
    for kind in ('nodes', 'statements'):
        for obj in graph.get(kind, []):
            _ensure(isinstance(obj, dict) and isinstance(obj.get('id'), str), 'élément de graphe invalide')
            by_id[obj['id']] = obj
    refs: list[str] = []
    for obligation in request['obligations']:
        for ref in obligation.get('source_refs', []):
            if ref not in refs: refs.append(ref)
        for sref in obligation['semantic_refs']:
            obj = by_id.get(sref)
            _ensure(obj is not None, 'référence sémantique inconnue dans une obligation : ' + sref)
            for ref in obj.get('source_refs', []):
                if ref not in refs: refs.append(ref)
    return refs


def _verify_pair(request: dict, result: dict, lang: str, key: str) -> dict[str, Any]:
    _ensure(request.get('schema_version') == '1.0' and result.get('schema_version') == '1.0', f'{key} : schéma SemantiK inconnu')
    rid = request.get('request_id')
    _ensure(isinstance(rid, str) and rid.strip(), f'{key} : request_id obligatoire')
    _ensure(isinstance(request.get('context'), dict) and request['context'].get('target_language') == lang, f'{key} : langue de la requête incorrecte')
    _ensure(result.get('language') == lang, f'{key} : langue du résultat incorrecte')
    locale = request['context'].get('target_locale')
    if locale:
        _ensure(result.get('locale') == locale, f'{key} : locale différente')
    _ensure(isinstance(request.get('obligations'), list) and bool(request['obligations']), f'{key} : obligations absentes')
    expected_ids = [o['obligation_id'] for o in request['obligations']]
    _ensure(len(set(expected_ids)) == len(expected_ids), f'{key} : obligations dupliquées')
    blocks = result.get('blocks')
    _ensure(isinstance(blocks, list) and bool(blocks), f'{key} : blocs absents')
    assembled, by_obligation = _from_blocks(blocks)
    _ensure(assembled and result.get('plain_text') == assembled and len(assembled) <= 5000, f'{key} : texte ne correspond pas aux blocs')
    coverage = result.get('coverage')
    _ensure(isinstance(coverage, list) and len(coverage) == len(expected_ids), f'{key} : couverture incomplète')
    got_ids = [c.get('obligation_id') for c in coverage if isinstance(c, dict)]
    _ensure(len(got_ids) == len(coverage) and set(got_ids) == set(expected_ids) and len(set(got_ids)) == len(got_ids), f'{key} : obligations non couvertes')
    for c in coverage:
        ids = c.get('block_ids')
        units = c.get('realization_unit_ids')
        _ensure(isinstance(ids, list) and ids and set(ids) == by_obligation.get(c['obligation_id'], set()), f'{key} : couverture des blocs incohérente')
        _ensure(isinstance(units, list) and units and len(set(units)) == len(units), f'{key} : unités de réalisation manquantes')
    sources = _source_refs(request)
    _ensure(result.get('source_refs', []) == sources and bool(sources), f'{key} : traçabilité sources absente ou incorrecte')
    runtime = result.get('runtime')
    _ensure(isinstance(runtime, dict) and isinstance(runtime.get('runtime_set_id'), str) and runtime['runtime_set_id'] and isinstance(runtime.get('sa_gf_contract_version'), str) and runtime['sa_gf_contract_version'], f'{key} : identité RuntimeSet absente')
    _ensure(runtime.get('capability_profile') == request.get('capability_profile'), f'{key} : profil de capacité différent')
    selector = request.get('runtime_selector')
    if isinstance(selector, dict) and selector.get('runtime_set_id'):
        _ensure(runtime['runtime_set_id'] == selector['runtime_set_id'], f'{key} : RuntimeSet non conforme au sélecteur')
    # Match SemantiK Architect CommunicationResult.compute_identity, excluding operational metadata.
    material = {k: v for k, v in result.items() if k not in {'operational', 'deterministic_result_id'}}
    blob = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(',', ':'), default=str).encode('utf-8')
    computed = 'sha256:' + hashlib.sha256(blob).hexdigest()
    _ensure(result.get('deterministic_result_id') == computed, f'{key} : identité déterministe du résultat incorrecte')
    return {
        'text': assembled,
        'status': 'fixture',
        'provider': 'semantik_architect',
        'channel': 'semantik_architect',
        'request_id': rid,
        'runtime_set_id': runtime['runtime_set_id'],
        'deterministic_result_id': computed,
        'source_refs': sources,
        'coverage': coverage,
    }


def prepare_mapping(article_path: Path, language: str, dest: Path) -> dict[str, Any]:
    """Create path placeholders only. No request, assertion or template inference."""
    article_path, dest = Path(article_path).resolve(), Path(dest).absolute()
    _ensure(language in {'fr', 'en', 'it'}, 'langue non prise en charge')
    _ensure(article_path.is_file() and not article_path.is_symlink(), 'article introuvable')
    _ensure(not dest.exists() and not dest.is_symlink() and dest.parent.is_dir(), 'fichier de correspondance déjà présent')
    article = _read(article_path)
    bindings = {}
    for key in sorted(_required_keys(article)):
        # Opaque, filesystem-safe stem, not a guessed semantic classification.
        suffix = hashlib.sha256(key.encode('utf-8')).hexdigest()[:12]
        prefix = re.sub(r'[^a-z0-9-]', '-', key.lower()).strip('-')[:32] or 'cle'
        name = prefix + '-' + suffix + '.json'
        bindings[key] = {'request': 'requests/' + name, 'result': 'results/' + name}
    document = {
        'format': TRANSFER_FORMAT, 'language': language,
        'note': 'CHEMINS A COMPLETER : aucune requête ni réalisation SemantiK produite par Spek.',
        'bindings': bindings,
    }
    # The mapping is only a local plan: no assertion/content is generated.
    with dest.open('x', encoding='utf-8') as fh:
        json.dump(document, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write('\n')
    return {'mapping': str(dest), 'language': language, 'required_keys': len(bindings)}


def transfer(article_path: Path, mapping_path: Path, out: Path, *, layouts: Path | None = None,
             state_snapshot: Path | None = None) -> dict[str, Any]:
    """Import already realized outputs, never invoke a RuntimeSet or auto-promote."""
    article_path, mapping_path, out = Path(article_path).absolute(), Path(mapping_path).absolute(), Path(out).absolute()
    _ensure(not article_path.is_symlink() and article_path.is_file(), 'article introuvable')
    _ensure(not mapping_path.is_symlink() and mapping_path.is_file(), 'transfert introuvable')
    _ensure(not out.exists() and not out.is_symlink() and out.parent.is_dir(), 'dossier de sortie doit être nouveau')
    _ensure(not any(p.is_symlink() for p in out.parents if p.exists()), 'sortie via un lien symbolique interdite')
    for source in (article_path, mapping_path):
        _ensure(not out.resolve().is_relative_to(source.parent), 'sortie dans les sources refusée')
    _ensure(not any((p / '.git').exists() for p in [out.parent, *out.parents]), 'sortie dans un dépôt Git interdite')
    article = _read(article_path)
    mapping = _read(mapping_path)
    _ensure(mapping.get('format') == TRANSFER_FORMAT, 'format de transfert inconnu')
    _ensure(set(mapping) <= {'format', 'language', 'bindings', 'note'}, 'champs supplémentaires non autorisés')
    lang = mapping.get('language')
    _ensure(lang in ('fr', 'en', 'it'), 'langue incompatible avec Spek')
    bindings = mapping.get('bindings')
    _ensure(isinstance(bindings, dict) and set(bindings) == _required_keys(article), 'une correspondance explicite est requise pour chaque clé utilisée dans l’article')
    entries: dict[str, dict] = {}
    record: dict[str, dict] = {}
    request_ids: set[str] = set()
    runtime_set_ids: set[str] = set()
    for key, paths in sorted(bindings.items()):
        _ensure(isinstance(paths, dict) and set(paths) == {'request', 'result'}, f'{key} : requête/résultat exigés')
        rp = _file(mapping_path.parent, paths['request'])
        op = _file(mapping_path.parent, paths['result'])
        request, result = _read(rp), _read(op)
        node = _verify_pair(request, result, lang, key)
        _ensure(node['request_id'] not in request_ids, f'{key} : request_id réutilisé')
        request_ids.add(node['request_id'])
        runtime_set_ids.add(node['runtime_set_id'])
        entries[key] = {lang: node}
        record[key] = {'request': str(rp), 'request_sha256': _hash_file(rp), 'result': str(op),
                       'result_sha256': _hash_file(op), 'request_id': node['request_id'],
                       'runtime_set_id': node['runtime_set_id'], 'deterministic_result_id': node['deterministic_result_id'],
                       'source_refs': node['source_refs']}
    _ensure(len(runtime_set_ids) == 1, 'RuntimeSets multiples pour une langue : segmentation explicite nécessaire')
    realizations = {'format': 'kristal.layout-realizations/0.1',
                    'note': 'Sorties SemantiK importées avec contrôles de cohérence; pas de revue humaine ni qualification par Spek. AUCUNE publication.',
                    'entries': entries}
    root = Path(__file__).resolve().parent.parent
    layouts = Path(layouts) if layouts is not None else root / 'layouts'
    _ensure(layouts.is_dir() and not layouts.is_symlink(), 'dossier layouts introuvable')
    layout_defs = [_read(x) for x in sorted(layouts.glob('*.json'))]
    snapshot = _read(Path(state_snapshot)) if state_snapshot else None
    # Strict Spek typed slots, source pin if required, one language; no publication approval.
    compile_inputs(article, realizations, layout_defs, languages=(lang,), state_snapshot=snapshot, production=False)
    report = {
        'format': 'spek.semantik-transfer-report/1.0',
        'status': 'PRIVATE_IMPORTED_NOT_QUALIFIED',
        'publication_eligible': False, 'runtime_authentication': 'NOT_PERFORMED',
        'source_authorization': 'NOT_GRANTED', 'language_review': 'NOT_PERFORMED', 'language': lang,
        'article_sha256': _hash_file(article_path),
        'mapping_sha256': _hash_file(mapping_path),
        'runtime_set_id_declared': next(iter(runtime_set_ids)),
        'realization_count': len(entries), 'bindings': record,
        'limit': 'Les identités SemantiK et leurs empreintes sont vérifiées comme données; ni signature ni RuntimeSet réel ne sont attestés ici.',
    }
    stage = Path(tempfile.mkdtemp(prefix='.spek-semantik-', dir=out.parent))
    try:
        (stage / 'realizations.json').write_text(json.dumps(realizations, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        (stage / 'transfer-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        os.rename(stage, out)
    finally:
        if stage.exists(): shutil.rmtree(stage)
    return {'directory': str(out), 'realizations': str(out / 'realizations.json'), 'report': str(out / 'transfer-report.json'), **{k: report[k] for k in ('status','language','realization_count','publication_eligible')}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Import privé de CommunicationResult SemantiK Architect dans Spek; jamais de qualification ni publication')
    parser.add_argument('--article', type=Path, required=True)
    parser.add_argument('--mapping', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--layouts', type=Path)
    parser.add_argument('--state-snapshot', type=Path)
    args = parser.parse_args(argv)
    try:
        result = transfer(args.article, args.mapping, args.out, layouts=args.layouts, state_snapshot=args.state_snapshot)
    except (ValidationError, OSError, ValueError) as exc:
        parser.exit(2, 'REFUS : ' + str(exc) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
