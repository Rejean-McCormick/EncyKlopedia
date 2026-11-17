"""Présentation déterministe du registre IA dans le Studio Spek.

Aucune analyse de Kristal, aucun choix automatique de template, aucune
qualification sémantique et aucun accès réseau. Les choix proviennent
exclusivement du registre IA enregistré dans Spek.
"""
from __future__ import annotations
from typing import Any


def display_name(slug: str, proposals: dict[str, dict]) -> str:
    record = proposals.get(slug) or {}
    title = str(record.get('title') or '').strip()
    return title or ('Kristal-' + slug.replace('-', ' ').title())


def filter_catalog(proposals: dict[str, dict], query: str) -> list[str]:
    """Recherche textuelle dans les choix déjà prescrits : jamais d'inférence."""
    query = ' '.join(query.casefold().split())
    return sorted(
        slug for slug in proposals
        if not query or query in slug.casefold() or query in display_name(slug, proposals).casefold()
    )


def resolve_display(proposals: dict[str, dict], slug: str | None,
                    observed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Distingue recherche au catalogue, source locale et revue structurelle.

    Un registre IA est toujours un projet éditorial, jamais une assignation
    approuvée. Un résultat d'inspection n'est utilisable que sur slug EXACT.
    """
    source = observed if observed and observed.get('identity') == slug else None
    proposal = proposals.get(slug) if slug else None
    review = source.get('structure_review') if source else None
    comparison = source.get('source_snapshot_comparison') if source else None
    verified = bool(review and comparison == 'MATCHES_UPLOADED_SNAPSHOT')
    if review:
        sections = [
            {'title': sec['heading'], 'type': sec.get('planned_template_id'), 'reviewed': True}
            for sec in review['ordered_structural_sections']
        ]
    elif proposal:
        sections = [
            {'title': sec['proposed_function'], 'type': sec['layout_id'], 'reviewed': False}
            for sec in proposal['ordered_sections']
        ]
    else:
        sections = []
    return {
        'slug': slug,
        'title': (source.get('title') if source else None) or (display_name(slug, proposals) if slug else None),
        'proposal': proposal,
        'has_local_source': source is not None,
        'source_verified': verified,
        'has_structural_review': review is not None or bool(proposal and proposal.get('canonical_review_status') == 'DEEP_SOURCE_INSPECTION_NOT_APPROVED'),
        'sections': sections,
        'publication_approved': False,
    }


def template_label(template_id: str | None) -> str:
    """Un nom lisible pour une présentation; ne change jamais le contrat."""
    if not template_id:
        return 'Gabarit non précisé'
    labels = {
        'agroecosystem-network': 'Réseau de l’agroécosystème',
        'mission-phase-map': 'Architecture des missions',
        'system-interface-map': 'Carte des systèmes et interfaces',
        'trajectory-constraints-map': 'Trajectoires et contraintes',
        'boundary-relation-map': 'Relations et frontières',
        'taxonomy-tree': 'Hiérarchie et classification',
        'concept-card': 'Fiche conceptuelle',
        'argument-map': 'Carte des arguments',
        'chronology': 'Chronologie',
        'comparison': 'Comparaison structurée',
        'evidence-comparison': 'Comparaison des preuves',
        'learning-path': 'Parcours pédagogique',
        'observation-inference': 'Observation et inférence',
        'result-card': 'Fiche de résultats',
    }
    return labels.get(template_id, template_id.replace('-', ' ').capitalize())
