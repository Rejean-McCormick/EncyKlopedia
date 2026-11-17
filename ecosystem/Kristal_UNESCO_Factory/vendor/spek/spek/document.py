"""Immutable, language-specific presentation projection.

This is a derived document model, NOT a Kristal canonical state. Renderers
consume the same projection and may not silently omit semantic identities.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
from typing import Mapping
from .core import Compiled


@dataclass(frozen=True)
class DocumentItem:
    id: str
    kind: str
    text: str
    status: str
    evidence_refs: tuple[str, ...]
    locator: str
    realization_key: str = ''
    realization_provider: str = ''
    realization_status: str = ''
    realization_request_id: str = ''
    realization_runtime_set_id: str = ''
    realization_channel: str = "legacy"
    realization_model_id: str = ""
    realization_generation_ref: str = ""
    realization_human_review_ref: str = ""
    external_ref: str = ""
    navigation_url: str = ""
    tokens: tuple[dict, ...] = ()
    evidence_details: tuple[dict, ...] = ()

    def trace(self) -> str:
        parts = [self.id, self.kind, self.status]
        if self.evidence_refs:
            parts.append('refs: ' + ', '.join(self.evidence_refs))
        if self.locator:
            parts.append('locator: ' + self.locator)
        if self.external_ref:
            parts.append('source-ref: ' + self.external_ref)
        if self.realization_channel != 'legacy':
            parts.append('language-channel: ' + self.realization_channel)
        if self.realization_model_id:
            parts.append('model: ' + self.realization_model_id)
        return ' · '.join(parts)

    def to_dict(self) -> dict:
        return dict(id=self.id, kind=self.kind, text=self.text, status=self.status,
                    evidence_refs=list(self.evidence_refs), locator=self.locator,
                    realization_key=self.realization_key,
                    realization_provider=self.realization_provider,
                    realization_status=self.realization_status,
                    realization_request_id=self.realization_request_id,
                    realization_runtime_set_id=self.realization_runtime_set_id,
                    realization_channel=self.realization_channel,
                    realization_model_id=self.realization_model_id,
                    realization_generation_ref=self.realization_generation_ref,
                    realization_human_review_ref=self.realization_human_review_ref,
                    external_ref=self.external_ref, navigation_url=self.navigation_url,
                    tokens=[dict(x) for x in self.tokens],
                    evidence_details=[dict(x) for x in self.evidence_details])


@dataclass(frozen=True)
class DocumentSection:
    id: str
    layout: str
    layout_version: str
    heading: str
    slots: Mapping[str, tuple[DocumentItem, ...]]

    def items(self, slot: str) -> tuple[DocumentItem, ...]:
        return self.slots.get(slot, ())

    def to_dict(self) -> dict:
        return dict(id=self.id, layout=self.layout, layout_version=self.layout_version,
                    heading=self.heading,
                    slots={slot: [item.to_dict() for item in entries]
                           for slot, entries in self.slots.items()})


@dataclass(frozen=True)
class SpekDocument:
    language: str
    article_id: str
    title: str
    subtitle: str
    abstract: str
    demonstration: bool
    source_verified: bool
    source_sha256: str
    realizations_sha256: str
    layouts_sha256: str
    sections: tuple[DocumentSection, ...]
    source_origin: str = ''
    source_state_ref: str = ''
    source_state_commitment: str = ''
    source_external_system: str = ''
    source_dataset_ref: str = ''
    source_reader_policy_ref: str = ''
    source_projection_sha256: str = ''

    def to_dict(self) -> dict:
        return dict(format='spek.document/0.4', language=self.language, article_id=self.article_id,
                    title=self.title, subtitle=self.subtitle, abstract=self.abstract,
                    demonstration=self.demonstration, source_verified=self.source_verified,
                    source_sha256=self.source_sha256, realizations_sha256=self.realizations_sha256,
                    layouts_sha256=self.layouts_sha256,
                    source_origin=self.source_origin,
                    source_state_ref=self.source_state_ref,
                    source_state_commitment=self.source_state_commitment,
                    source_external_system=self.source_external_system,
                    source_dataset_ref=self.source_dataset_ref,
                    source_reader_policy_ref=self.source_reader_policy_ref,
                    source_projection_sha256=self.source_projection_sha256,
                    sections=[section.to_dict() for section in self.sections])


def project_document(model: Compiled, language: str) -> SpekDocument:
    if language not in model.languages:
        raise ValueError('Language not validated in model: ' + language)
    sections = []
    for section in model.sections:
        slots = {}
        for slot in model.layouts[section['layout']]['slots']:
            entries = []
            for source in model.slot_items(section, slot, language):
                semantic = model.units.get(source['id']) or model.evidence[source['id']]
                realized = model.realizations['entries'][semantic['realization_key']][language]
                annotated = {(x['start'], x['end']): x for x in realized.get('tokens', [])}
                # This only separates surface strings; it never infers grammar or meaning.
                tokens = []
                for hit in re.finditer(r"\w+(?:[’'-]\w+)*|[^\w\s]", source['text'], re.UNICODE):
                    start, end = hit.span()
                    explicit = annotated.get((start, end))
                    tokens.append(dict(surface=hit.group(), start=start, end=end,
                        lemma=(explicit or {}).get('lemma',''),
                        pos=(explicit or {}).get('pos',''),
                        features=(explicit or {}).get('features',{}),
                        lexeme_ref=(explicit or {}).get('lexeme_ref',''),
                        semantic_ref=(explicit or {}).get('semantic_ref',''),
                        gf_function=(explicit or {}).get('gf_function',''),
                        annotation_status=(explicit or {}).get('annotation_status','surface_only')))
                evidence_details = tuple(dict(id=eid,
                    text=model.item(eid, language)['text'],
                    status=model.evidence[eid]['status'],
                    locator=model.evidence[eid]['locator'])
                    for eid in source.get('evidence_refs', []))
                entries.append(DocumentItem(
                    id=source['id'], kind=source['kind'], text=source['text'],
                    status=source.get('epistemic_status') or 'unspecified',
                    evidence_refs=tuple(source.get('evidence_refs') or ()),
                    locator=source.get('locator') or '',
                    realization_key=semantic['realization_key'],
                    realization_provider=realized['provider'],
                    realization_status=realized['status'],
                    realization_request_id=realized.get('request_id',''),
                    realization_runtime_set_id=realized.get('runtime_set_id',''),
                    realization_channel=realized.get('channel', 'legacy'),
                    realization_model_id=realized.get('model_id',''),
                    realization_generation_ref=realized.get('generation_ref',''),
                    realization_human_review_ref=realized.get('human_review',{}).get('review_ref',''),
                    external_ref=semantic.get('external_ref',''),
                    navigation_url=semantic.get('navigation_url',''),
                    tokens=tuple(tokens), evidence_details=evidence_details))
            slots[slot] = tuple(entries)
        sections.append(DocumentSection(id=section['id'],layout=section['layout'],
                         layout_version=model.layouts[section['layout']]['version'],
                         heading=model.text(section['heading_key'], language),slots=slots))
    article=model.source['article']
    return SpekDocument(language=language, article_id=article['id'],
       title=model.text(article['title_key'],language),
       subtitle=model.text(article['subtitle_key'],language),
       abstract=model.text(article['abstract_key'],language),
       demonstration=model.demo, source_verified=model.source_verified,
       source_sha256=model.source_hash, realizations_sha256=model.realization_hash,
       layouts_sha256=model.layout_hash, sections=tuple(sections),
       source_origin=model.source['source']['origin'],
       source_state_ref=model.source['source'].get('state_ref') or '',
       source_state_commitment=model.source['source'].get('state_commitment') or '',
       source_external_system=model.source['source'].get('external_system') or '',
       source_dataset_ref=model.source['source'].get('dataset_ref') or '',
       source_reader_policy_ref=model.source['source'].get('reader_policy_ref') or '',
       source_projection_sha256=model.source['source'].get('projection_sha256') or '')
