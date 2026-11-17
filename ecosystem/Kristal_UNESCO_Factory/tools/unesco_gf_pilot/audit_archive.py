"""Offline, read-only verifier for a UNESCO -> GF -> SemantiK -> Spek pilot ZIP.

This verifies archived *evidence consistency*, not a live execution, a GF
language-quality review, RuntimeSet release, or editorial authorization.

Usage: python tools/unesco_gf_pilot/audit_archive.py path/to/Kristal_UNESCO_Pilote_*.zip
       python ... --json path/to/audit.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

MAX_FILE = 25_000_000
MAX_TOTAL = 200_000_000
LANGS = ("fr", "en")


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit(archive: Path) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    checks: list[str] = []
    languages: dict[str, dict] = {}
    with zipfile.ZipFile(archive) as z:
        entries = z.infolist()
        names = [i.filename for i in entries]
        if len(names) != len(set(names)):
            raise ValueError("Entrées ZIP dupliquées; archive rejetée")
        for i in entries:
            p = PurePosixPath(i.filename)
            if (p.is_absolute() or '..' in p.parts or '\\' in i.filename or
                    i.file_size > MAX_FILE or i.compress_size > MAX_FILE):
                raise ValueError("Entrée ZIP non sûre / trop grande : " + i.filename)
        if sum(x.file_size for x in entries) > MAX_TOTAL:
            raise ValueError("Archive trop volumineuse")
        available = set(names)

        def read(name: str) -> bytes:
            if name not in available:
                errors.append("Fichier absent : " + name)
                return b''
            return z.read(name)

        def js(name: str) -> dict:
            raw = read(name)
            if not raw:
                return {}
            try:
                val = json.loads(raw.decode('utf-8-sig'))
                if isinstance(val, dict):
                    return val
                errors.append("JSON non objet : " + name)
            except (UnicodeDecodeError, ValueError) as exc:
                errors.append(f"JSON invalide : {name}: {exc}")
            return {}

        report = js('report.json')
        source = js('source-provenance.json')
        if report.get('status') != 'CANDIDATE_VERIFIED_PRIVATE_NOT_RELEASED':
            errors.append('Statut pilote inattendu : ' + str(report.get('status')))
        if report.get('publication_authorized') is not False or report.get('qualified_released_runtime') is not False:
            errors.append('Une autorisation release/publication serait incohérente pour ce pilote')
        if report.get('errors'):
            errors.append('Erreurs déclarées dans report.json')
        if source.get('concept_id') != report.get('concept_id'):
            errors.append('Identité UNESCO incohérente entre source et rapport')
        concept_id = str(report.get('concept_id') or '')
        if not re.fullmatch(r'concept\d+', concept_id):
            errors.append('Concept ID invalide')
        if source.get('status') != 'source_only_not_canonical':
            errors.append('La source UNESCO n’est pas marquée non canonique')

        for lang in LANGS:
            prefix = f'candidates/{lang}/'
            r = report.get('languages', {}).get(lang, {})
            b = js(prefix + 'wordbench-build.json')
            lock = js(prefix + 'pipeline.lock.json')
            suite = js(prefix + 'conformance.suite.json')
            conform = js(prefix + 'conformance.report.json')
            preflight = js(prefix + 'orchestrator-preflight.json')
            verified = js(f'verified/{lang}/{concept_id}.json')
            pgf = read(prefix + 'grammar.pgf')
            actual_hash = hash_bytes(pgf) if pgf else ''
            if not pgf:
                errors.append(f'{lang}: PGF absent')
            elif len(pgf) < 8:
                errors.append(f'{lang}: PGF anormalement court')
            for name, claim in [('report.json', r.get('gf_sha256')),
                                ('wordbench-build.json', b.get('pgf_sha256')),
                                ('pipeline.lock.json', lock.get('inputs', {}).get('grammar.pgf')),
                                ('orchestrator-preflight.json', preflight.get('pgf_sha256'))]:
                if claim != actual_hash:
                    errors.append(f'{lang}: SHA256 PGF ne correspond pas à {name}')
            if not (b.get('exit_code') == 0 and b.get('process_state') == 'completed' and
                    b.get('capture_complete') is True and b.get('pgf_compiled') is True and
                    b.get('status') == 'PGF_BUILT_CANDIDATE_ONLY'):
                errors.append(f'{lang}: Compilation Wordbench non confirmée')
            if not (conform.get('passed') is True and
                    len(conform.get('results', [])) == 2 and
                    all(x.get('passed') is True for x in conform['results'])):
                errors.append(f'{lang}: Conformité SemantiK non établie (2 cas attendus)')
            if preflight.get('status') != 'PRIVATE_CANDIDATE_EVIDENCE_CHECKED_NOT_RELEASED':
                errors.append(f'{lang}: Preflight orchestrateur non concluant')
            if r.get('status') != 'CANDIDATE_GF_SEMANTIK_SPEK_VERIFIED_NOT_RELEASED':
                errors.append(f'{lang}: Statut pilote non vérifié')
            if (suite.get('language'), lock.get('language')) != (lang, lang):
                errors.append(f'{lang}: Langue candidate incohérente')
            if not (suite.get('runtime_set_id') == lock.get('runtime_set_id') == preflight.get('runtime_set_id')):
                errors.append(f'{lang}: Identité runtime incohérente')
            for fn, digest in lock.get('inputs', {}).items():
                expected = prefix + fn
                if expected not in available or hash_bytes(z.read(expected)) != digest:
                    errors.append(f'{lang}: Fichier verrouillé manquant ou modifié : {fn}')
            verified_entries = verified.get('entries', {})
            for kind in ('scope', 'statement'):
                stem = f'{concept_id}.{lang}.{kind}'
                req = js(f'requests/{lang}/{stem}.json')
                res = js(f'results/{lang}/{stem}.json')
                if req.get('context', {}).get('target_language') != lang or res.get('language') != lang:
                    errors.append(f'{lang}/{kind}: langue requête/résultat incohérente')
                req_obligations = {o.get('obligation_id') for o in req.get('obligations', [])}
                res_coverage = {c.get('obligation_id') for c in res.get('coverage', [])}
                if not req_obligations or req_obligations != res_coverage:
                    errors.append(f'{lang}/{kind}: couverture des obligations incohérente')
                blocks = res.get('blocks', [])
                if len(blocks) != 1 or blocks[0].get('text') != res.get('plain_text'):
                    errors.append(f'{lang}/{kind}: texte/bloques SemantiK incohérents')
                actual_src = []
                statements = {s['id']: s for s in req.get('semantic_graph', {}).get('statements', []) if 'id' in s}
                for obligation in req.get('obligations', []):
                    for source_ref in obligation.get('source_refs', []):
                        if source_ref not in actual_src:
                            actual_src.append(source_ref)
                    for semref in obligation.get('semantic_refs', []):
                        for source_ref in statements.get(semref, {}).get('source_refs', []):
                            if source_ref not in actual_src:
                                actual_src.append(source_ref)
                if res.get('source_refs') != actual_src or not actual_src:
                    errors.append(f'{lang}/{kind}: provenance source incohérente')
                mat = {k: v for k, v in res.items() if k not in ('operational', 'deterministic_result_id')}
                canon = json.dumps(mat, ensure_ascii=False, sort_keys=True,
                                   separators=(',', ':'), default=str).encode('utf-8')
                expected_id = 'sha256:' + hash_bytes(canon)
                if res.get('deterministic_result_id') != expected_id:
                    errors.append(f'{lang}/{kind}: résultat SemantiK altéré')
                transfer = verified_entries.get(stem, {}).get(lang, {})
                if not transfer or transfer.get('text') != res.get('plain_text') or transfer.get('deterministic_result_id') != expected_id:
                    errors.append(f'{lang}/{kind}: correspondance Spek non établie')
                if transfer.get('status') == 'fixture':
                    # Existing Spek transfer label; do not upgrade it to editorial/release proof.
                    warnings.append(f'{lang}/{kind}: le transfert Spek utilise le statut interne « fixture »; ce n’est pas une qualification éditoriale')
                if res.get('runtime', {}).get('runtime_set_id') != lock.get('runtime_set_id'):
                    errors.append(f'{lang}/{kind}: runtime déclaré différent du candidat')
                page = read(f'wiki_prive/{concept_id}.{lang}.md').decode('utf8', 'replace')
                if res.get('plain_text') and res['plain_text'] not in page:
                    errors.append(f'{lang}/{kind}: texte SemantiK absent du wiki privé')
            grammar = read(prefix + 'UnescoPilot.gf').decode('utf8', 'replace')
            concrete = read(prefix + ('UnescoPilotFre.gf' if lang == 'fr' else 'UnescoPilotEng.gf')).decode('utf8', 'replace')
            if 'String -> String -> String' in grammar and '++' in concrete:
                warnings.append(f'{lang}: grammaire GF minimale de concaténation de chaînes; pas de preuve d’usage RGL')
            languages[lang] = {'pgf_bytes':len(pgf), 'pgf_sha256':actual_hash,
                               'conformance_passed':conform.get('passed') is True,
                               'cases':len(conform.get('results', [])),
                               'compiled':b.get('pgf_compiled') is True,
                               'output_markdown':f'wiki_prive/{concept_id}.{lang}.md'}
        if report.get('publication_authorized') is False:
            checks.append('Publication correctement interdite')
        if all(language.get('compiled') and language.get('conformance_passed') for language in languages.values()):
            checks.append('Compilations et conformités FR/EN déclarées, preuves internes vérifiées')

    return {'audit_format': 'unesco-evidence-audit/1.0',
            'archive':archive.name, 'concept_id':concept_id,
            'status':'EVIDENCE_CONSISTENT_CANDIDATE_NOT_RELEASED' if not errors else 'EVIDENCE_INCONSISTENT',
            'errors':errors,'warnings':warnings,'checks':checks,
            'languages':languages,
            'scope':'Intégrité et cohérence de pièces archivées; aucune nouvelle exécution GF, aucune revue éditoriale.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('zip', type=Path)
    p.add_argument('--json', type=Path)
    a = p.parse_args()
    try:
        outcome = audit(a.zip)
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError, KeyError, TypeError, IndexError) as exc:
        outcome={'status':'AUDIT_UNAVAILABLE','errors':[f'{type(exc).__name__}: {exc}']}
    result=json.dumps(outcome,ensure_ascii=False,indent=2)+'\n'
    if a.json:
        a.json.write_text(result,encoding='utf-8')
    print(result)
    return 0 if outcome.get('status') == 'EVIDENCE_CONSISTENT_CANDIDATE_NOT_RELEASED' else 2


if __name__ == '__main__':
    raise SystemExit(main())
