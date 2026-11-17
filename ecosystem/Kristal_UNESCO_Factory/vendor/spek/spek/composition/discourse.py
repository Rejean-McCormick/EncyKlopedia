"""Static discourse contracts for Spek recursive templates.

These models describe *how* explicitly selected SemantiK utterances are ordered
and visually grouped. They neither verify rhetorical truth nor fabricate lexical
connectors, semantic assertions, argument warrants or editorial authorization.
"""
from __future__ import annotations

from typing import Any
from spek.core import ValidationError

FORMAT = 'spek.discourse-model/1.0'
NUCLEARITY = {'nucleus', 'satellite', 'multinuclear', 'focus', 'supporting'}
ROLE = {'section_heading', 'lead_sentence', 'paragraph', 'supporting_sentence',
        'qualification', 'caption', 'embedded_template'}


def validate_discourse(definition: dict[str, Any]) -> tuple[str, ...]:
    """Validate a complete deterministic slot-to-discourse mapping.

    Returns paragraph start slots (excluding the initial paragraph). Legacy
    template graphs without a model retain their earlier behavior.
    """
    model = definition.get('discourse_model')
    if model is None:
        return tuple(definition.get('presentation_policy', {}).get('paragraph_break_before_slots', []))
    if not isinstance(model, dict) or model.get('format') != FORMAT:
        raise ValidationError('Modèle discursif non reconnu')
    if model.get('scope') != 'editorial_adaptation_not_a_normative_semantic_validator':
        raise ValidationError('Portée du modèle discursif non définie')
    slots = definition['ordered_slots']
    if model.get('focus_slot') not in slots:
        raise ValidationError('Point focal absent du modèle discursif')
    rcontract = definition.get('rhetorical_contract')
    expected_tag = (rcontract['relationship_label'] if rcontract else
                    'structural.' + definition['template_id'].split('.',1)[1])
    if model.get('relation_tag') != expected_tag:
        raise ValidationError('Relation discursive différente du contrat éditorial')
    moves = model.get('moves')
    groups = model.get('paragraph_groups')
    if not isinstance(moves, list) or not isinstance(groups, list) or not groups:
        raise ValidationError('Mouvements ou paragraphes discursifs absents')
    if any(not isinstance(g, list) or not g or len(g) > 100 for g in groups):
        raise ValidationError('Groupe de paragraphe invalide')
    flat = [slot for g in groups for slot in g]
    if flat != slots:
        raise ValidationError('Les paragraphes ne couvrent pas exactement les slots ordonnés')
    if len(moves) != len(slots) or [m.get('slot') for m in moves if isinstance(m, dict)] != slots:
        raise ValidationError('Chaque slot doit porter un mouvement discursif, dans l’ordre')
    slot_to_group = {slot:i+1 for i,g in enumerate(groups) for slot in g}
    for move in moves:
        slot=move['slot']
        if (not isinstance(move.get('function'), str) or not move['function'] or
            not all(c.islower() or c.isdigit() or c in '_-' for c in move['function']) or
            move.get('nuclearity') not in NUCLEARITY or
            type(move.get('group')) is not int or move['group'] != slot_to_group[slot]):
            raise ValidationError('Rôle discursif non déterministe : ' + slot)
        required_role = definition['slots'][slot].get('visual_role',
            'embedded_template' if definition['slots'][slot]['node_kind']=='child' else 'paragraph')
        if move.get('surface_role') != required_role or move['surface_role'] not in ROLE:
            raise ValidationError('Rôle visuel discordant du slot : ' + slot)
    links = model.get('links')
    if not isinstance(links, list):
        raise ValidationError('Liens discursifs manquants')
    seen: set[tuple[str,str,str]] = set()
    parents: dict[str,str] = {}
    for link in links:
        if not isinstance(link, dict):
            raise ValidationError('Lien discursif non structuré')
        a,b,r = link.get('from_slot'), link.get('to_slot'), link.get('relation')
        expected_status = 'requires_external_semantic_review' if rcontract else 'presentation_only'
        if (a not in slots or b not in slots or a==b or r !=
            (expected_tag if rcontract else 'structural.arrangement') or
            link.get('status') != expected_status or (a,b,r) in seen or
            not isinstance(link.get('relation_function'),str) or
            not link['relation_function'] or
            not all(c.islower() or c.isdigit() or c in '_-' for c in link['relation_function'])):
            raise ValidationError('Lien discursif non autorisé')
        seen.add((a,b,r))
        if a in parents:
            raise ValidationError('Un même mouvement ne peut avoir deux liens hiérarchiques implicites')
        parents[a]=b
    if (len(links) != len(slots)-1 or set(parents) != set(slots)-{model['focus_slot']}):
        raise ValidationError('Tous les mouvements secondaires doivent rejoindre la relation focale')
    # Explicit discourse DAG: all moves reach the focal move, with no cycles.
    for origin in parents:
        node=origin;visited=set()
        while node != model['focus_slot']:
            if node in visited or node not in parents:
                raise ValidationError('Cycle ou fragment discursif déconnecté')
            visited.add(node)
            node=parents[node]
    cohesion = model.get('cohesion')
    if not isinstance(cohesion, dict) or (
        cohesion.get('connectives') != 'only_explicit_semantik_realizations' or
        cohesion.get('rewrite_existing_phrases') is not False or
        cohesion.get('infer_relations_from_adjacent_slots') is not False or
        cohesion.get('text_without_realization') != 'refuse' or
        cohesion.get('transition_slot_policy') != 'optional_explicit_text_slot_only'):
        raise ValidationError('Politique de cohésion incompatible avec Spek–SemantiK')
    review=model.get('semantic_review')
    if (not isinstance(review,dict) or review.get('checked_by_spek') is not False or
        review.get('required_for_publication') is not True or
        not isinstance(review.get('warning'),str) or not review['warning'].strip() or
        not isinstance(review.get('questions'),list) or
        not all(isinstance(q,str) for q in review['questions'])):
        raise ValidationError('Le modèle discursif doit expliciter les limites de validation')
    breaks=tuple(g[0] for g in groups[1:])
    presentation=definition.get('presentation_policy',{})
    if presentation.get('layout_variant','flow')=='flow':
        if tuple(presentation.get('paragraph_break_before_slots',[])) != breaks:
            raise ValidationError('Rendu et paragraphes discursifs discordants')
    # Stack/two_column already have block boundaries, while discourse groups still
    # describe the logical movements without overriding layout geometry.
    return breaks


def discourse_audit(resolved: Any) -> dict[str, Any]:
    """Reader-safe structural report: never exports source assertions or hashes."""
    from .engine import Node
    nodes: list[dict[str, Any]] = []
    def visit(node):
        if not isinstance(node,Node):return
        model=node.discourse_model
        if model:
            moves=[]
            byslot={m['slot']:m for m in model['moves']}
            for slot,children in node.ordered:
                if children:
                    m=byslot[slot]
                    moves.append({'function':m['function'], 'nuclearity':m['nuclearity'],
                                  'paragraph':m['group'], 'units':len(children)})
            nodes.append({'pattern':node.template_ref, 'moves':moves,
                          'relations_declared_unverified':sum(1 for l in model['links']
                              if l['status']=='requires_external_semantic_review'),
                          'connectors_generated':0,
                          'semantic_truth_checked':False})
        for _,children in node.ordered:
            for child in children:visit(child)
    visit(resolved.root)
    return {'format':'spek.discourse-audit/1.0','status':'private_not_approved',
            'templates_with_discourse_model':len(nodes),
            'declared_relations_unverified':sum(x['relations_declared_unverified'] for x in nodes),
            'connectors_generated':0,
            'content_selection_performed':False,
            'nodes':nodes}
