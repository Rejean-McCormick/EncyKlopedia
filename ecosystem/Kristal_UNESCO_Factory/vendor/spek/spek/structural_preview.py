"""Offline, source-backed *structural audit* of AI-prescribed Kristal sections.

This preview does not implement production Spek editorial layouts or SemantiK,
does not select assertions for public disclosure, and cannot publish anything.
No heuristic classification, template discovery, temporal/casual inference, or
substituted prose: the reviewed source coordinates drive the entire display.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
import tempfile
from typing import Any

from .core import ValidationError
from .branding import logo_svg
from .studio_workflow import inspect_kristal

FORMAT = 'spek.wiki-structural-preview-contracts/1.0'
MANIFEST_FORMAT = 'spek.private-structural-audit/1.0'
_ID = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')
_FAMILIES = {'network', 'chain', 'matrix', 'ledger', 'taxonomy', 'trajectory', 'provenance'}


def load_preview_contracts(root: Path) -> dict[str, dict]:
    """Explicit list of human/AI-authored preview kinds, never derived from Kristal data."""
    path = Path(root)/'template_library'/'wiki'/'structural-preview-contracts.json'
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 150_000:
        raise ValidationError('Contrats d’inspection structurelle manquants ou non admissibles')
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise ValidationError('Contrats d’inspection structurelle illisibles') from exc
    if (not isinstance(data, dict) or data.get('format') != FORMAT
            or data.get('publication_eligible') is not False
            or data.get('template_inference_allowed') is not False
            or data.get('production_layouts_implemented') is not True):
        raise ValidationError('Contrats structurels non conformes à la séparation édition/publication')
    items = data.get('templates')
    if not isinstance(items, list) or len(items) != 19:
        raise ValidationError('Le catalogue structurel doit contenir 19 gabarits explicites')
    contracts = {}
    for item in items:
        if not isinstance(item,dict) or not _ID.fullmatch(str(item.get('id',''))):
            raise ValidationError('Identifiant structurel invalide')
        if (item['id'] in contracts or item.get('preview_kind') not in _FAMILIES
                or item.get('status') != 'AUDIT_PREVIEW_ONLY'
                or not isinstance(item.get('label'),str) or not item['label']):
            raise ValidationError('Contrat de gabarit structurel ambigu')
        contracts[item['id']] = item
    # These previews are strictly a view of the existing 19 explicitly specified templates.
    backlog = Path(root)/'template_library'/'wiki'/'specialized-template-designs.json'
    expected = json.loads(backlog.read_text(encoding='utf-8'))
    if set(contracts) != {t['id'] for t in expected.get('templates', [])}:
        raise ValidationError('Les contrats d’aperçu divergent du registre des gabarits à développer')
    return contracts


def _h(value: Any) -> str:
    return escape(str(value), quote=True)


def _read_source(folder: Path, review: dict) -> tuple[list[dict], str]:
    base = Path(folder).resolve(strict=True)
    rel = Path(review['source']['portable_state_relative_path'])
    if rel.is_absolute() or any(p in ('..','.') for p in rel.parts):
        raise ValidationError('Chemin source non autorisé dans la revue')
    target = base
    for part in rel.parts:
        target = target/part
        if target.is_symlink():
            raise ValidationError('Lien symbolique interdit dans le chemin source')
    if not target.resolve(strict=False).is_relative_to(base):
        raise ValidationError('Chemin source hors Kristal')
    if not target.is_file() or target.stat().st_size > 20_000_000:
        raise ValidationError('État portable absent ou trop volumineux')
    content = target.read_bytes()
    current = sha256(content).hexdigest()
    if current != review['source']['portable_state_raw_sha256']:
        raise ValidationError('La source locale diffère du snapshot étudié : nouvelle revue nécessaire')
    try:
        state = json.loads(content)
    except ValueError as exc:
        raise ValidationError('État portable JSON invalide') from exc
    if (not isinstance(state,dict) or state.get('schema_version') != '6.0'
            or state.get('artifact_type') != 'kristal_state'
            or not isinstance(state.get('assertions'),list)):
        raise ValidationError('État Kristal portable v8/v6 inattendu')
    assertions = state['assertions']
    if len(assertions) != review['source']['assertion_occurrences']:
        raise ValidationError('Nombre d’assertions différent de la revue')
    if any(not isinstance(a,dict) for a in assertions):
        raise ValidationError('Assertion mal formée')
    return assertions, current


def _render_document(info: dict, review: dict, assertions: list[dict], digest: str, contracts: dict) -> str:
    """Plan privé, sans triplets bruts ou texte improvisé; digest jamais émis."""
    slug = info['identity']
    title = info.get('title') or slug
    sections = review['ordered_structural_sections']
    links: list[str] = []
    blocks: list[str] = []
    for idx, part in enumerate(sections, 1):
        template = part['planned_template_id']
        contract = contracts[template]
        sec_id = 's'+str(idx)
        links.append(f'<a href="#{sec_id}"><span class="nav-num">{idx:02d}</span>'
                     f'<span>{_h(part["heading"])}</span></a>')
        blocks.append(
            f'<section class="section-card" id="{sec_id}" aria-labelledby="h-{sec_id}">'
            f'<p class="section-label">Partie {idx} · Plan documentaire</p>'
            f'<h2 id="h-{sec_id}">{_h(part["heading"])}</h2>'
            f'<p class="sub">Présentation prévue · {_h(contract["label"])}</p>'
            '<div class="pending">'
            '<strong>Texte en attente de réalisation SemantiK</strong>'
            '<p>Cette section est prévue dans la composition. Les phrases seront '
            'affichées ici uniquement après sélection des faits, réalisation '
            'linguistique par SemantiK Architect et contrôle des résultats.</p>'
            '</div>'
            '</section>'
        )
    risks = '<li>La composition doit être revue et les faits sélectionnés avant toute publication.</li>'
    logo = logo_svg()
    # No original source hash, path, evidence IDs or audit manifest is shipped
    # in the HTML, even as hidden markup or script state.
    return f'''<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; form-action 'none'; base-uri 'none'">
<title>{_h(title)} · Atelier Spek · plan privé</title>
<style>
:root{{color-scheme:light;--accent:#1e6864;--dark:#154d4a;--soft:#e4f2ef;--paper:#f6f9f8;--ink:#142329;--muted:#64717a;--line:#dbe7e4;font-family:system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--paper);color:var(--ink)}}
*{{box-sizing:border-box}} html{{scroll-behavior:smooth}}body{{margin:0;line-height:1.55}}
.skip{{position:absolute;top:-100px;left:16px;background:var(--accent);color:white;padding:8px 14px;z-index:10}}.skip:focus{{top:12px}}
header{{background:white;border-bottom:1px solid var(--line)}}
.brand-row{{max-width:1500px;margin:auto;min-height:90px;padding:16px 34px;display:flex;align-items:center;gap:20px}}
.brand-mark{{flex:none;width:80px;height:auto}}
.brand-copy{{border-left:1px solid var(--line);padding-left:22px}}.brand-copy strong{{display:block;font-size:1.12rem;letter-spacing:.01em}}.brand-copy .object{{color:var(--accent);font-weight:750;font-size:1.05rem}}
.brand-copy .slug{{font-weight:500;color:var(--muted);font-size:.92rem}}
.wrapper{{max-width:1500px;margin:auto;padding:22px 26px 72px}}
.hero{{border:1px solid #d7e9e5;background:linear-gradient(105deg,#eff8f6,#deeeeb);border-radius:15px;padding:22px 25px;display:flex;justify-content:space-between;gap:18px;align-items:center;margin-bottom:25px}}
.hero h1{{font-size:clamp(1.13rem,2vw,1.45rem);line-height:1.35;margin:0 0 6px}}.hero p{{margin:0;color:#445a5b}}
.pills{{display:flex;align-items:center;gap:9px;flex-wrap:wrap}}.pill{{font-size:.8rem;border:1px solid #cfe3de;background:#fff;border-radius:50px;padding:9px 12px;color:var(--dark);font-weight:700;white-space:nowrap}}
.shell{{display:grid;grid-template-columns:minmax(220px,285px) minmax(0,1fr);gap:22px;align-items:start}}
nav{{position:sticky;top:16px;background:#fff;border:1px solid var(--line);border-radius:15px;padding:19px 14px;box-shadow:0 3px 17px #13392f0c}}nav h2{{font-size:1.15rem;padding:0 10px;margin:6px 0 18px}}
nav a{{display:flex;gap:12px;align-items:center;color:#253a3c;text-decoration:none;border-radius:8px;padding:10px 11px;margin:2px 0;font-size:.91rem}}nav a:hover,nav a:focus-visible{{background:var(--soft);color:var(--dark)}}.nav-num{{color:var(--accent);font-weight:800}}
nav a:last-child{{border-top:1px solid var(--line);border-radius:0;margin-top:16px;padding-top:16px}}main{{min-width:0}}
.section-card{{scroll-margin-top:20px;background:#fff;border:1px solid var(--line);border-radius:15px;padding:26px 28px;margin-bottom:20px;box-shadow:0 4px 18px #173d330c}}
.section-label{{color:var(--accent);text-transform:uppercase;letter-spacing:.08em;font-size:.76rem;font-weight:800;margin:0 0 12px}}
.section-card h2{{font-size:1.55rem;margin:0 0 5px;letter-spacing:-.02em}}.sub{{color:var(--muted);font-size:.87rem;margin:0 0 20px}}.sub code{{font-family:inherit;color:#4b6463}}.description{{font-size:1rem;margin:0 0 17px;max-width:72ch}}
.notice{{background:#fdf8eb;border-left:3px solid #bb8825;color:#6e551f;padding:13px 16px;border-radius:0 7px 7px 0;margin:15px 0 20px;font-size:.9rem}}
.relations{{border-top:1px solid #e8efed;padding-top:13px}}details>summary{{cursor:pointer;color:var(--accent);font-weight:750;list-style:none;padding:8px 0}}details>summary::before{{content:'›';display:inline-block;margin-right:10px;font-size:1.4rem;vertical-align:-1px}}details[open]>summary::before{{transform:rotate(90deg)}}.summary-help{{font-size:.83rem;font-weight:450;color:var(--muted)}}.source-help{{color:var(--muted);font-size:.87rem}}
.relation{{border:1px solid var(--line);border-radius:9px;margin:10px 0;padding:13px 15px;background:#fbfdfc;overflow-wrap:anywhere}}
.rel-grid{{display:grid;grid-template-columns:minmax(0,1fr) minmax(90px,auto) minmax(0,1fr);gap:14px;align-items:center}}.operator{{color:var(--accent);font-size:.88rem;text-align:center}}.term{{overflow-wrap:anywhere}}
.table-scroll{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;font-size:.87rem}}th,td{{border-bottom:1px solid var(--line);text-align:left;padding:11px;overflow-wrap:anywhere}}th{{background:var(--soft)}}.pending{{border:1px solid var(--line);background:var(--soft);border-radius:11px;padding:18px 20px;color:var(--dark)}}.pending strong{{display:block;margin-bottom:5px}}.pending p{{margin:0;color:#47645f}}.empty{{color:var(--muted)}}.footer-note{{color:var(--muted);font-size:.86rem;margin:24px 6px}}
a:focus-visible,summary:focus-visible{{outline:3px solid #71aba6;outline-offset:3px}}
@media(max-width:900px){{.hero{{display:block}}.pills{{margin-top:16px}}.shell{{grid-template-columns:1fr}}nav{{position:static}}nav a{{display:inline-flex;margin:2px 1px}}nav a:last-child{{border-top:none;padding:10px 11px;margin-top:2px}}}}
@media(max-width:560px){{.brand-row{{padding:13px 18px}}.brand-mark{{width:52px}}.brand-copy{{padding-left:12px}}.brand-copy strong{{font-size:.9rem}}.wrapper{{padding:14px}}.section-card{{padding:21px 18px}}.hero{{padding:19px 17px}}.rel-grid{{display:block}}.operator{{display:block;padding:5px 0;text-align:left}}.summary-help{{display:none}}}}
@media print{{nav,.relations,.pills{{display:none}}.section-card{{break-inside:avoid;box-shadow:none}}.wrapper{{padding:10px}}}}
</style></head>
<body><a class="skip" href="#content">Passer au contenu</a>
<header><div class="brand-row">{logo}<div class="brand-copy"><strong>SPEK · Atelier de composition</strong>
<span class="object">{_h(title)}</span> <span class="slug">({_h(slug)})</span></div></div></header>
<div class="wrapper"><div class="hero"><div><h1>Plan documentaire privé — textes en attente</h1>
<p>Plan de lecture préparé. Les textes des sections doivent être réalisés par SemantiK Architect.</p></div>
<div class="pills"><span class="pill">◈ Plan privé</span><span class="pill">▤ {len(sections)} sections</span><span class="pill">✎ Réalisation en attente</span></div></div>
<div class="shell"><nav aria-label="Plan du Kristal"><h2>Plan du Kristal</h2>{''.join(links)}<a href="#risks">Limites et précautions</a></nav>
<main id="content"><p class="notice">Cet écran est un plan documentaire, pas une publication. Les données canoniques brutes ne sont pas affichées comme du texte.</p>
{''.join(blocks)}<section class="section-card" id="risks"><p class="section-label">À consulter</p><h2>Limites et précautions</h2><ul>{risks}</ul>
<p>Pour voir un véritable Wiki rédigé, utilise « Réaliser avec SemantiK » dans l’atelier, avec un article et des requêtes explicites, puis « Prévisualiser le Wiki ».</p></section>
<p class="footer-note">SPEK · Atelier local de composition · Document privé, sans autorisation de publication.</p>
</main></div></div></body></html>'''


def create_structural_preview(spek_root: Path, kristal_folder: Path, *, output: Path | None=None) -> dict[str, Any]:
    """Build an offline HTML source audit ONLY for one of the five reviewed Kristals.

    Fails closed when source hashes differ or no reviewed positions exist. A
    private temporary directory is used by default, outside the source repo.
    """
    spek_root=Path(spek_root).resolve(strict=True)
    kristal_folder=Path(kristal_folder).resolve(strict=True)
    info=inspect_kristal(kristal_folder,spek_root)
    review=info.get('structure_review')
    if not info.get('proposal') or not review:
        raise ValidationError('Aucune revue canonique détaillée disponible pour ce Kristal (122 en attente)')
    contracts=load_preview_contracts(spek_root)
    for section in review['ordered_structural_sections']:
        if section['planned_template_id'] not in contracts:
            raise ValidationError('Gabarit spécialisé sans contrat d’aperçu')
    assertions,digest=_read_source(kristal_folder,review)
    html=_render_document(info,review,assertions,digest,contracts)
    if output is None:
        folder=Path(tempfile.mkdtemp(prefix='spek-audit-prive-'))
    else:
        folder=Path(output).expanduser().resolve()
        if folder.exists():
            raise ValidationError('Dossier de sortie déjà existant')
        if folder.is_relative_to(kristal_folder) or folder.is_relative_to(spek_root):
            raise ValidationError('La sortie ne peut pas être dans le Kristal ou dans Spek')
        folder.mkdir(parents=False,exist_ok=False)
    page=folder/'inspection-structurelle.html'
    page.write_text(html,encoding='utf-8')
    manifest={
        'format':MANIFEST_FORMAT,
        'publication_eligible':False,'approval':'NONE','semantik_realized':False,
        'kristal_slug':info['identity'],
        'assertion_occurrences':len(assertions),
        'sections':[{'id':s['section_id'],'template_id':s['planned_template_id'],
                     'observed_occurrences':len(s['source_observation']['source_positions_zero_based'])}
                    for s in review['ordered_structural_sections']],
        'page_sha256':sha256(page.read_bytes()).hexdigest(),
        'warning':'LOCAL SOURCE AUDIT ONLY; NEVER TRANSFER AS A GITHUB WIKI PUBLICATION',
    }
    (folder/'inspection-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return {'page':str(page),'directory':str(folder),'manifest':manifest,'status':'PRIVATE_SOURCE_AUDIT_NOT_PUBLISHABLE'}
