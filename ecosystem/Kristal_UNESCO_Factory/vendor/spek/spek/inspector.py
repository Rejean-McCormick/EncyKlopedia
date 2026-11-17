"""Static, accessible, structured source panels for each semantic card.

All details are rendered locally; no JavaScript, network, raw JSON or invented
morphological analysis. `<details>`/`<summary>` are keyboard-operable toggles.
"""
from __future__ import annotations
import html
from .document import DocumentItem, SpekDocument
from .locale import INSPECTOR_UI


def esc(s: object) -> str:
    return html.escape(str(s), quote=True)


def _value(s: object, t: dict) -> str:
    return esc(s) if s not in (None, '') else f'<em class="not-provided">{esc(t["not_supplied"])}</em>'


def _attribute(label: str, val: object, t: dict) -> str:
    return f'<div class="source-attribute"><dt>{esc(label)}</dt><dd>{_value(val,t)}</dd></div>'


def _token_table(item: DocumentItem, t: dict) -> str:
    header=''.join(f'<th scope="col">{esc(t[k])}</th>' for k in ('word','lemma','pos','features','links','annotation'))
    rows=[]
    for tok in item.tokens:
        fields=tok.get('features') or {}
        features=', '.join(f'{k}: {v}' for k,v in sorted(fields.items()))
        links=', '.join(filter(None, (tok.get('lexeme_ref'),tok.get('semantic_ref'),tok.get('gf_function'))))
        status=t.get(tok['annotation_status'], tok['annotation_status'])
        rows.append(f'<tr data-start="{tok["start"]}" data-end="{tok["end"]}">'
           f'<th scope="row">{esc(tok["surface"])}</th>'
           f'<td>{_value(tok.get("lemma"),t)}</td><td>{_value(tok.get("pos"),t)}</td>'
           f'<td>{_value(features,t)}</td><td>{_value(links,t)}</td><td>{esc(status)}</td></tr>')
    return (f'<h5>{esc(t["words"])}</h5><p class="source-note">{esc(t["token_note"])}</p>'
            f'<div class="token-scroll" tabindex="0" role="region" aria-label="{esc(t["words"])}">'
            f'<table class="token-table"><thead><tr>{header}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')


def _evidence(item: DocumentItem, t: dict) -> str:
    records=list(item.evidence_details)
    if item.kind=='evidence':
        records.insert(0,dict(id=item.id, text=item.text, status=item.status, locator=item.locator))
    if not records:
        return f'<p class="source-note">{esc(t["none"])}</p>'
    parts=[]
    for r in records:
        parts.append('<div class="evidence-entry">'
            f'<strong>{esc(r["id"])}</strong><p>{esc(r["text"])}</p><dl>'
            +_attribute(t['proof_status'],r['status'],t)
            +_attribute(t['locator'],r['locator'],t)
            +'</dl></div>')
    return ''.join(parts)


def _unit_source(item: DocumentItem, doc: SpekDocument, t: dict) -> str:
    details=(f'<article class="source-record" data-source-id="{esc(item.id)}">'
       f'<h4>{esc(t["unit"])} <code>{esc(item.id)}</code></h4>'
       f'<h5>{esc(t["origin"])}</h5><dl class="source-attributes">'
       +_attribute(t['kind'],item.kind,t)
       +_attribute(t['epistemic'],item.status,t)
       +_attribute(t['origin_type'],doc.source_origin,t)
       +_attribute(t['state'],doc.source_state_ref,t)
       +_attribute(t['commitment'],doc.source_state_commitment,t)
       +_attribute(t['external_ref'],item.external_ref,t)
       +_attribute(t['system'],doc.source_external_system,t)
       +_attribute(t['dataset'],doc.source_dataset_ref,t)
       +_attribute(t['policy'],doc.source_reader_policy_ref,t)
       +_attribute(t['projection'],doc.source_projection_sha256,t)
       +'</dl>'
       +(f'<a class="source-navigation" href="{esc(item.navigation_url)}" target="_blank" rel="noopener noreferrer">{esc(t["open_graph"])} ↗</a>' if item.navigation_url else '')
       +f'<h5>{esc(t["realization"])}</h5><dl class="source-attributes">'
       +_attribute(t['key'],item.realization_key,t)
       +_attribute(t['provider'],item.realization_provider,t)
       +_attribute(t['realization_status'],item.realization_status,t)
       +_attribute(t['request'],item.realization_request_id,t)
       +_attribute(t['runtime'],item.realization_runtime_set_id,t)
       +_attribute(t['channel'],item.realization_channel,t)
       +_attribute(t['model'],item.realization_model_id,t)
       +_attribute(t['generation'],item.realization_generation_ref,t)
       +_attribute(t['review'],item.realization_human_review_ref,t)
       +'</dl>'
       +_token_table(item,t)
       +f'<h5>{esc(t["proofs"])}</h5>'
       +_evidence(item,t)
       +'</article>')
    return details


def card_inspector(items: tuple[DocumentItem,...], doc: SpekDocument, *, slot: str) -> str:
    """One toggle per visible card, displaying typed source data of each member."""
    t=INSPECTOR_UI[doc.language]
    body=''.join(_unit_source(item, doc, t) for item in items)
    return (f'<details class="source-inspector" data-inspector-slot="{esc(slot)}">'
            f'<summary class="source-trigger"><span aria-hidden="true">◇</span> {esc(t["open"])}'
            f'<span class="source-trigger-caret" aria-hidden="true">▾</span></summary>'
            f'<div class="source-panel">{body}</div></details>')
