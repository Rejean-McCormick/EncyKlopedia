"""Unified recursive template interpreter and private reader preview.

One engine for all categories. No fact inference, HTTP, arbitrary code or
fallback prose. Presentation only arranges verbatim, externally realized text.
"""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
import json
import re
from pathlib import Path
from typing import Any

from spek.core import ValidationError
from spek.slot_dialogue import KIND_POLICY, compose_request
from .discourse import validate_discourse

DEFINITIONS_FORMAT = 'spek.template-graph/1.0'
INSTANCE_FORMAT = 'spek.composition-instance/1.0'
PLAN_FORMAT = 'spek.recursive-dialogue/1.0'
SAFE_ID = re.compile(r'[a-z][a-z0-9._-]{0,95}\Z')
REF = re.compile(r'([a-z][a-z0-9-]{0,49})\.([a-z][a-z0-9-]{0,75})@([0-9]+\.[0-9]+\.[0-9]+)\Z')
ALLOWED_ROLES = {'section_heading', 'lead_sentence', 'paragraph', 'supporting_sentence', 'qualification', 'caption'}
ALLOWED_LAYOUTS = {'flow', 'stack', 'two_column', 'compact_list'}
MAX_DEPTH, MAX_NODES, MAX_REPEAT = 8, 2000, 100
MAX_BYTES = 2_000_000
SENSITIVE = re.compile(r'(?:source_digest|source_sha256|runtime_set_id|request_id|referent\s*:|(?:^|\s)urn:|\bfile://|[a-zA-Z]:\\\\?[^\s]+|\bstring\s*:|\b[a-f0-9]{64}\b)', re.I)


def _object(value: Any, context: str) -> dict:
    if not isinstance(value, dict):
        raise ValidationError(f'{context}: objet JSON attendu')
    return value


def _safe_id(value: Any, context: str) -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise ValidationError(f'{context}: identifiant invalide')
    return value


def _ref(value: Any) -> tuple[str, str, str]:
    match = REF.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        raise ValidationError('Référence de template invalide ou non versionnée')
    return match.groups()


def _json_file(path: Path, root: Path) -> dict:
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValidationError('Chemin de définition invalide ou lien symbolique')
    if path.stat().st_size > MAX_BYTES:
        raise ValidationError('Définition trop volumineuse')
    try:
        return _object(json.loads(path.read_text(encoding='utf-8')), 'définition')
    except (ValueError, OSError) as exc:
        raise ValidationError('Définition JSON illisible') from exc


def _validate_definition(obj: dict, category: str, filename: str) -> None:
    if obj.get('format') != DEFINITIONS_FORMAT or obj.get('category') != category:
        raise ValidationError('Contrat de définition incorrect')
    ident = obj.get('template_id')
    version = obj.get('version')
    _ref(f'{ident}@{version}')
    if ident != f'{category}.{filename}':
        raise ValidationError('ID de définition différent du fichier')
    slots = _object(obj.get('slots'), 'slots')
    ordered = obj.get('ordered_slots')
    if not slots or not isinstance(ordered, list) or len(ordered) != len(set(ordered)) or set(ordered) != set(slots):
        raise ValidationError('Séquence des slots manquante, dupliquée ou non concordante')
    for slot, rule in slots.items():
        _safe_id(slot, 'slot')
        rule = _object(rule, 'règle de slot')
        kind = rule.get('node_kind')
        if kind not in {'text', 'child'}:
            raise ValidationError('Type de slot inconnu')
        mn, mx = rule.get('min'), rule.get('max')
        if type(mn) is not int or type(mx) is not int or not 0 <= mn <= mx <= MAX_REPEAT:
            raise ValidationError('Cardinalité de slot invalide')
        allowed = rule.get('allowed_kinds' if kind == 'text' else 'allowed_templates')
        if not isinstance(allowed, list) or not allowed or len(set(allowed)) != len(allowed):
            raise ValidationError('Types autorisés absents ou dupliqués')
        if kind == 'text':
            if any(x not in KIND_POLICY for x in allowed):
                raise ValidationError('Type linguistique non pris en charge')
        else:
            for ref in allowed:
                _ref(ref)  # exact version is mandatory, never a wildcard
    policy = _object(obj.get('presentation_policy', {}), 'presentation')
    if policy.get('layout_variant', 'flow') not in ALLOWED_LAYOUTS:
        raise ValidationError('Disposition non autorisée')
    if policy.get('show_template_labels', False) is not False:
        raise ValidationError('Étiquettes techniques interdites dans le rendu')
    breaks = policy.get('paragraph_break_before_slots', [])
    if (not isinstance(breaks, list) or len(breaks) != len(set(breaks))
        or not set(breaks).issubset(set(ordered))
        or (breaks and policy.get('layout_variant', 'flow') != 'flow')):
        raise ValidationError('Frontières de paragraphes incompatibles avec les slots ou le mode')
    if obj.get('no_fact_selection') is not True or obj.get('no_text_generation') is not True:
        raise ValidationError('Une définition ne peut choisir les faits ni générer de texte')
    contract = obj.get('rhetorical_contract')
    if contract is not None:
        contract = _object(contract, 'contrat rhétorique')
        rel = contract.get('relationship_label')
        if (not isinstance(rel, str) or not re.fullmatch(r'[a-z]+(?:[.-][a-z]+)*', rel)):
            raise ValidationError('Relation rhétorique invalide')
        if contract.get('editorial_relation_required') is not True:
            raise ValidationError('La relation doit être explicitement déclarée par le processus éditorial')
        if not isinstance(contract.get('semantic_warning'), str) or not contract['semantic_warning'].strip():
            raise ValidationError('Avertissement sémantique rhétorique requis')
        if not isinstance(contract.get('critical_questions'), list) or not all(isinstance(q, str) for q in contract['critical_questions']):
            raise ValidationError('Questions critiques rhétoriques invalides')
    validate_discourse(obj)


class Library:
    """Load trusted, local, versioned definitions with exact matching."""
    def __init__(self, root: Path):
        raw_root = Path(root)
        if raw_root.is_symlink():
            raise ValidationError('Bibliothèque symbolique interdite')
        self.root = raw_root.resolve()
        if not self.root.is_dir() or self.root.is_symlink():
            raise ValidationError('Bibliothèque absente ou lien symbolique')
        self.definitions: dict[str, dict] = {}
        for category in sorted(self.root.iterdir()):
            if not category.is_dir():
                continue
            if category.is_symlink() or not SAFE_ID.fullmatch(category.name):
                raise ValidationError('Catégorie de templates invalide')
            folder = category / 'templates'
            if not folder.exists():
                continue
            if folder.is_symlink() or not folder.is_dir():
                raise ValidationError('Dossier de templates non sûr')
            for file in sorted(folder.glob('*.json')):
                obj = _json_file(file, self.root)
                if obj.get('format') != DEFINITIONS_FORMAT:
                    continue  # legacy category-template contracts are separate
                _validate_definition(obj, category.name, file.stem)
                ref = f"{obj['template_id']}@{obj['version']}"
                if ref in self.definitions:
                    raise ValidationError('Définition dupliquée')
                self.definitions[ref] = obj

    def get(self, ref: str) -> dict:
        _ref(ref)
        if ref not in self.definitions:
            raise ValidationError('Template/version introuvable : ' + ref)
        return self.definitions[ref]


@dataclass(frozen=True)
class Leaf:
    key: str
    request_ref: str
    kind: str
    role: str
    path: str
    discourse_function: str = ''
    discourse_nuclearity: str = ''
    discourse_group: int = 0
    discourse_relation: str = ''
    source_assertion_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class Node:
    template_ref: str
    path: str
    layout: str
    ordered: tuple[tuple[str, tuple['Node | Leaf', ...]], ...]
    paragraph_break_before_slots: tuple[str, ...] = ()
    discourse_model: dict | None = None


@dataclass(frozen=True)
class Resolved:
    root: Node
    leaves: tuple[Leaf, ...]
    instance_id: str
    private_status: str = 'composition_resolved_not_approved'


def resolve(instance: dict, library: Library) -> Resolved:
    """Expand only explicit children and repeat instances. No inference."""
    instance = _object(instance, 'instance')
    if instance.get('format') != INSTANCE_FORMAT:
        raise ValidationError('Format d’instance vNext non reconnu')
    ident = _safe_id(instance.get('instance_id'), 'instance_id')
    _ref(instance.get('template_ref'))
    policy = _object(instance.get('presentation', {}), 'présentation')
    if policy.get('join_mode', 'block') != 'block':
        raise ValidationError('Seul le mode de jointure block est implémenté')
    if policy.get('show_template_labels', False) is not False:
        raise ValidationError('Les étiquettes techniques ne sont pas rendues')
    if policy.get('layout_variant', 'flow') not in ALLOWED_LAYOUTS:
        raise ValidationError('Layout de composition invalide')
    if instance.get('authority') != 'editorial_bindings_explicit_not_approved':
        raise ValidationError('Autorité éditoriale explicite requise')
    leaves: list[Leaf] = []
    keys: set[str] = set()
    paths: set[str] = set()
    counter = 0

    def expand(value: dict, path: str, depth: int, stack: tuple[str, ...], expected: str | None = None) -> Node:
        nonlocal counter
        if depth > MAX_DEPTH:
            raise ValidationError('Profondeur maximale dépassée')
        counter += 1
        if counter > MAX_NODES:
            raise ValidationError('Trop de nœuds dans la composition')
        value = _object(value, 'instance de template')
        if value.get('node_type', 'template_ref') != 'template_ref':
            raise ValidationError('Un enfant doit être une référence de template')
        ref = value.get('template_ref')
        if expected and ref != expected:
            raise ValidationError('Référence de template différente de la répétition')
        definition = library.get(ref)
        # An attestation here is only an explicit editorial declaration, NOT a
        # semantic proof or C1/C2/C3 approval. The actual assertion links must
        # still be checked by the external editorial/publication process.
        contract = definition.get('rhetorical_contract')
        if contract is not None:
            declaration = _object(value.get('editorial_relation'), 'déclaration de relation rhétorique')
            if declaration.get('relation_tag') != contract['relationship_label']:
                raise ValidationError('La relation rhétorique doit être déclarée exactement')
            if declaration.get('status') != 'declared_unverified':
                raise ValidationError('Statut explicite non vérifié requis')
            refs = declaration.get('source_assertion_refs')
            if (not isinstance(refs, list) or not refs or len(refs) > 30
                or len(refs) != len(set(refs))
                or any(not isinstance(x, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}', x) for x in refs)):
                raise ValidationError('Références éditoriales explicites requises pour la relation')
        if ref in stack:
            raise ValidationError('Cycle de templates détecté : ' + ref)
        if path in paths:
            raise ValidationError('Chemin d’instance dupliqué')
        paths.add(path)
        bindings = _object(value.get('bindings'), 'bindings')
        rules = definition['slots']
        if set(bindings) - set(rules):
            raise ValidationError('Slot inconnu dans les bindings')
        ordered = []
        discourse = definition.get('discourse_model')
        moves = {m['slot']:m for m in discourse['moves']} if discourse else {}
        for slot in definition['ordered_slots']:
            rule = rules[slot]
            bind = bindings.get(slot)
            if bind is None:
                values = []
            elif isinstance(bind, dict) and bind.get('node_type') == 'repeat':
                if rule['node_kind'] != 'child':
                    raise ValidationError('Répétition réservée aux enfants')
                repeat = bind
                repeat_ref = repeat.get('template_ref')
                if repeat_ref not in rule['allowed_templates']:
                    raise ValidationError('Template répété non permis')
                values = repeat.get('instances')
                if not isinstance(values, list) or len(values) > MAX_REPEAT:
                    raise ValidationError('Répétition trop grande ou invalide')
                if (type(repeat.get('min')) is not int or type(repeat.get('max')) is not int
                        or not 0 <= repeat['min'] <= len(values) <= repeat['max'] <= MAX_REPEAT):
                    raise ValidationError('Cardinalité explicite de répétition violée')
            else:
                values = bind if isinstance(bind, list) else [bind]
            if not rule['min'] <= len(values) <= rule['max']:
                raise ValidationError('Cardinalité de slot violée : ' + slot)
            children: list[Node | Leaf] = []
            ids: set[str] = set()
            for pos, item in enumerate(values, 1):
                item = _object(item, 'binding')
                item_id = item.get('instance_id', f'item{pos}')
                _safe_id(item_id if isinstance(item_id, str) else '', 'instance enfant')
                if item_id in ids:
                    raise ValidationError('Identifiants d’instances répétés dans le même slot')
                ids.add(item_id)
                childpath = f'{path}/{slot}@{item_id}'
                if rule['node_kind'] == 'child':
                    ref_child = item.get('template_ref')
                    if ref_child not in rule['allowed_templates']:
                        raise ValidationError('Sous-template non permis')
                    if isinstance(bind, dict) and bind.get('node_type') == 'repeat' and ref_child != bind['template_ref']:
                        raise ValidationError('Template enfant différent du repeat')
                    children.append(expand(item, childpath, depth+1, (*stack, ref)))
                else:
                    if item.get('node_type') != 'text_slot':
                        raise ValidationError('Un slot text doit avoir node_type=text_slot')
                    kind = item.get('kind') or (rule['allowed_kinds'][0] if len(rule['allowed_kinds']) == 1 else None)
                    if kind not in rule['allowed_kinds']:
                        raise ValidationError('Type linguistique absent ou incompatible')
                    key = _safe_id(item.get('realization_key'), 'clé de réalisation')
                    request_ref = item.get('communication_request_ref')
                    if (not isinstance(request_ref, str) or not re.fullmatch(r'requests/[a-zA-Z0-9._-]+\.json', request_ref)):
                        raise ValidationError('Référence de requête non sûre ou absente')
                    if key in keys:
                        raise ValidationError('Clé de réalisation réutilisée implicitement')
                    keys.add(key)
                    # Logical roles are based on explicit slot declaration, never fact content.
                    role = rule.get('visual_role', 'paragraph')
                    if role not in ALLOWED_ROLES:
                        raise ValidationError('Rôle visuel inconnu')
                    refs = item.get('source_assertion_refs', [])
                    if (not isinstance(refs, list) or len(refs)>30 or len(refs)!=len(set(refs)) or
                        any(not isinstance(x,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}', x) for x in refs)):
                        raise ValidationError('Références d’assertion explicites invalides')
                    move = moves.get(slot, {})
                    leaf = Leaf(key=key, request_ref=request_ref, kind=kind, role=role, path=childpath,
                        discourse_function=move.get('function',''), discourse_nuclearity=move.get('nuclearity',''),
                        discourse_group=move.get('group',0),
                        discourse_relation=discourse['relation_tag'] if discourse else '',
                        source_assertion_refs=tuple(refs))
                    leaves.append(leaf)
                    children.append(leaf)
                    counter += 1
                    if counter > MAX_NODES:
                        raise ValidationError('Trop de nœuds')
            ordered.append((slot, tuple(children)))
        layout = definition.get('presentation_policy', {}).get('layout_variant', 'flow')
        if depth == 0:
            layout = policy.get('layout_variant', layout)
        return Node(ref, path, layout, tuple(ordered),
                    tuple(definition.get('presentation_policy', {}).get('paragraph_break_before_slots', [])),
                    discourse)

    root = expand(instance, ident, 0, ())
    return Resolved(root, tuple(leaves), ident)


def dialogue_plan(resolved: Resolved, language: str, *, requests: dict[str, dict] | None = None) -> dict:
    """Describe SemantiK language constraints for each explicit leaf.

    If requests are given, intersect them through the existing SemantiK adapter,
    preserving semantic_graph and obligations exactly. They are private data.
    """
    if language not in {'fr','en','it'}:
        raise ValidationError('Langue non prise en charge')
    fields = []
    for leaf in resolved.leaves:
        intent, force, kinds, limit = KIND_POLICY[leaf.kind]
        field = {'instance_path': leaf.path, 'slot_kind': leaf.kind, 'realization_key': leaf.key,
                 'communication_request_ref': leaf.request_ref,
                 'form': {'intent': intent, 'force': force, 'block_kinds': kinds, 'max_length': limit},
                 'presentation': {'visual_role': leaf.role, 'join_mode': 'block'},
                 'discourse': {'function':leaf.discourse_function,
                               'nuclearity':leaf.discourse_nuclearity,
                               'paragraph_group':leaf.discourse_group,
                               'declared_relation_unverified':leaf.discourse_relation,
                               'connective_generated':False}}
        if requests is not None:
            request = requests.get(leaf.request_ref)
            if not isinstance(request, dict):
                raise ValidationError('Requête SemantiK manquante : ' + leaf.request_ref)
            # Validation and intersection only, no new obligations.
            updated = compose_request(request, {'force': force, 'block_kinds': kinds, 'max_length': limit}, language=language)
            if updated['semantic_graph'] != request['semantic_graph'] or updated['obligations'] != request['obligations']:
                raise ValidationError('Une obligation ou un fait a été modifié')
            field['form']['block_kinds'] = updated['constraints']['allowed_block_kinds']
            field['form']['max_length'] = updated['constraints']['max_length']
        fields.append(field)
    return {'format': PLAN_FORMAT, 'status': 'private_not_approved', 'language': language,
            'instance_id': resolved.instance_id, 'fields': fields}


def _plain_realizations(resolved: Resolved, bundle: dict, language: str) -> dict[str, str]:
    bundle = _object(bundle, 'réalisations SemantiK')
    if bundle.get('format') != 'kristal.layout-realizations/0.1':
        raise ValidationError('Format de réalisations incompatible')
    entries = _object(bundle.get('entries'), 'entrées')
    data: dict[str, str] = {}
    for leaf in resolved.leaves:
        row = _object(entries.get(leaf.key), 'réalisation manquante')
        val = _object(row.get(language), 'langue manquante dans réalisation')
        text = val.get('text')
        if not isinstance(text, str) or not text.strip() or len(text) > 5000:
            raise ValidationError('Réalisation textuelle absente ou trop longue')
        if SENSITIVE.search(text):
            raise ValidationError('La réalisation contient une donnée technique potentiellement privée')
        if val.get('status') not in {'fixture','realized','verified','production_candidate'} or not val.get('provider'):
            raise ValidationError('Provenance de réalisation absente')
        data[leaf.key] = text.strip()
    return data


def materialize(resolved: Resolved, bundle: dict, language: str) -> dict[str, str]:
    """Resolve all leaves or refuse. Output is still a PRIVATE preview only."""
    if language not in {'fr','en','it'}:
        raise ValidationError('Langue invalide')
    return _plain_realizations(resolved, bundle, language)


def _escape_md(value: str) -> str:
    # Reading output only: escape Markdown syntax and HTML, not natural-language
    # punctuation. A SemantiK realization never becomes executable markup.
    value = escape(value, quote=False).replace('\n', ' ').replace('\r', ' ')
    return re.sub(r'([\\`*_{}\[\]()#+!|>~-])', r'\\\1', value)


def _walk_md(node: Node | Leaf, values: dict[str, str], *, level: int = 1) -> str:
    if isinstance(node, Leaf):
        text = _escape_md(values[node.key])
        if node.role == 'lead_sentence':
            return '**' + text + '**'
        if node.role == 'section_heading':
            return '#' * min(6, level) + ' ' + text
        return text
    parts = []
    for slot, children in node.ordered:
        if node.layout == 'flow' and slot in node.paragraph_break_before_slots and parts:
            parts.append('\n\n')
        for child in children:
            value = _walk_md(child, values, level=level + (1 if isinstance(child, Node) and child.layout == 'stack' else 0))
            if value:
                parts.append(value)
    if node.layout == 'compact_list':
        return '\n'.join('- ' + p for p in parts)
    if node.layout == 'stack':
        return '\n\n'.join(parts)
    if node.layout == 'flow':
        groups: list[list[str]] = [[]]
        for part in parts:
            if part == '\n\n':
                if groups[-1]: groups.append([])
            else: groups[-1].append(part)
        return '\n\n'.join(' '.join(g) for g in groups if g)
    return ' '.join(parts)


def _validate_reader_values(resolved: Resolved, values: dict[str, str]) -> None:
    if not isinstance(values, dict) or set(values) != {leaf.key for leaf in resolved.leaves}:
        raise ValidationError('Réalisation manquante ou supplémentaire')
    for value in values.values():
        if not isinstance(value, str) or not value.strip() or len(value) > 5000 or SENSITIVE.search(value):
            raise ValidationError('Réalisation invalide ou contenant une donnée interne')


def render_markdown(resolved: Resolved, values: dict[str, str], *, title: str = 'Aperçu privé') -> str:
    _validate_reader_values(resolved, values)
    if SENSITIVE.search(title):
        raise ValidationError('Titre contenant une donnée privée')
    title = _escape_md(title)
    return '# ' + title + '\n\n> Aperçu privé — non publiable sans qualification et autorisation.\n\n' + _walk_md(resolved.root, values) + '\n'


def _walk_html(node: Node | Leaf, values: dict[str, str]) -> str:
    """Flow layouts flatten templates into prose without nested <p> or <h2>."""
    if isinstance(node, Leaf):
        txt = escape(values[node.key], quote=True)
        if node.role == 'lead_sentence':
            return '<strong>' + txt + '</strong>'
        if node.role == 'section_heading':
            return '<h2>' + txt + '</h2>'
        if node.role == 'qualification':
            return '<span class="qualification">' + txt + '</span>'
        return txt

    children = [child for _, group in node.ordered for child in group]
    if node.layout == 'flow':
        # The semantic tree may have many nested templates, but each leaf is a
        # complete SemantiK utterance. No punctuation or grammar is rewritten.
        lines: list[str] = []
        paragraph: list[str] = []
        def flush():
            if paragraph:
                lines.append('<p>' + ' '.join(paragraph) + '</p>')
                paragraph.clear()
        for slot, group in node.ordered:
            if slot in node.paragraph_break_before_slots:
                flush()
            for child in group:
                if isinstance(child, Node) and child.layout == 'flow' and not child.paragraph_break_before_slots:
                    # flatten this definition boundary: no extra card or title
                    for fragment in _inline_flow(child, values):
                        paragraph.append(fragment)
                elif isinstance(child, Leaf) and child.role != 'section_heading':
                    paragraph.append(_walk_html(child, values))
                else:
                    flush()
                    lines.append(_walk_html(child, values))
        flush()
        return ''.join(lines)
    if node.layout == 'stack':
        result: list[str] = []
        for child in children:
            if isinstance(child, Node):
                result.append(_walk_html(child, values))
            elif child.role == 'section_heading':
                result.append(_walk_html(child, values))
            else:
                result.append('<p>' + _walk_html(child, values) + '</p>')
        return ''.join(result)
    if node.layout == 'compact_list':
        return '<ul>' + ''.join('<li>' + _walk_html(c, values) + '</li>' for c in children) + '</ul>'
    if node.layout == 'two_column':
        # Semantically ordered DOM; responsive CSS changes only geometry.
        return '<div class="comparison-flow">' + ''.join('<div>' + _walk_html(c, values) + '</div>' for c in children) + '</div>'
    raise ValidationError('Disposition inconnue')


def _inline_flow(node: Node, values: dict[str, str]) -> list[str]:
    """Flatten flow-only descendants; delegate any non-flow nodes separately."""
    result: list[str] = []
    for _, group in node.ordered:
        for child in group:
            if isinstance(child, Node) and child.layout == 'flow' and not child.paragraph_break_before_slots:
                result.extend(_inline_flow(child, values))
            elif isinstance(child, Leaf):
                if child.role == 'section_heading':
                    raise ValidationError('Titre structurant imbriqué dans une phrase fluide')
                result.append(_walk_html(child, values))
            else:
                raise ValidationError('Disposition de groupe incompatible avec la jointure fluide')
    return result


def render_html(resolved: Resolved, values: dict[str, str], *, title: str = 'Aperçu privé', language: str = 'fr') -> str:
    if language not in {'fr', 'en', 'it'}:
        raise ValidationError('Langue invalide')
    _validate_reader_values(resolved, values)
    if SENSITIVE.search(title):
        raise ValidationError('Titre contenant une donnée privée')
    body = _walk_html(resolved.root, values)
    return (f'<!doctype html><html lang="{language}"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{escape(title)}</title><style>'
            ':root{--brand:#1e6864}body{font-family:system-ui,Segoe UI,sans-serif;margin:0;background:#f7faf9;color:#1b312f;line-height:1.65}'
            'main{max-width:860px;margin:3rem auto;padding:2rem;background:white;border:1px solid #d9e6e2;border-radius:12px}'
            'h1{color:var(--brand);line-height:1.2}.notice{color:#566b67;border-left:4px solid var(--brand);padding:.75rem;margin:1rem 0;background:#e8f4f1}'
            '.comparison-flow{display:grid;grid-template-columns:1fr 1fr;gap:1rem}.comparison-flow>div{min-width:0}'
            '.qualification{color:#685122}.comparison-flow>div:nth-child(even){background:#f1f7f5;padding:.5rem;border-radius:5px}'
            '@media(max-width:650px){main{margin:0;padding:1rem}.comparison-flow{grid-template-columns:1fr}}'
            '</style></head><body><main><h1>'+escape(title)+'</h1>'
            '<p class="notice">Aperçu privé — non publiable sans qualification et autorisation.</p>'
            '<article>'+body+'</article></main></body></html>')
