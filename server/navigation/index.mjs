import { canonical } from '../pack.mjs';

const add = (map, key, value) => {
  const list = map.get(key) || [];
  list.push(value);
  map.set(key, list);
};

function qualifierInfo(q) {
  const predicate = q?.predicate?.external_id || q?.predicate?.id || q?.predicate;
  if (typeof predicate !== 'string' || !predicate) return null;
  const predicateLabel = q?.predicate?.label || predicate;
  const object = q?.object;
  if (!object || typeof object !== 'object') return null;
  if (object.kind === 'item' && object.value && typeof object.value === 'object') {
    const id = object.value.external_id || object.value.id;
    const label = object.value.label || id;
    if (typeof id !== 'string' || !id) return null;
    return { predicate, predicateLabel, kind: 'item', key: canonical(id), id, label };
  }
  const raw = object.value;
  if (!['string', 'number', 'boolean'].includes(typeof raw)) return null;
  return {
    predicate,
    predicateLabel,
    kind: object.kind || typeof raw,
    key: canonical(raw),
    value: raw,
    label: String(raw),
  };
}

export class NavigationIndex {
  constructor(engine, state) {
    this.engine = engine;
    this.state = state;
    this.byEntity = new Map();
    this.entityEdges = new Map();
    this.bySource = new Map();
    this.byRelationValue = new Map();
    this.byQualifier = new Map();
    this.byQualifierItem = new Map();
    this.qualifiersByAssertion = new Map();
    for (const a of state.assertions.values()) {
      add(this.byEntity, a.subject, a);
      const rel = engine.relations.get(a.relation);
      add(this.entityEdges, a.subject, { assertion: a, relationId: a.relation, value: a.value, direction: 'outgoing' });
      if (rel?.valueKind === 'entity') {
        add(this.byEntity, a.value, a);
        add(this.entityEdges, a.value, {
          assertion: a,
          relationId: rel.inverseOf || a.relation,
          value: a.subject,
          direction: 'incoming',
        });
      }
      add(this.byRelationValue, `${a.relation}|${canonical(a.value)}`, a);
      for (const source of a.sourceRefs || []) add(this.bySource, source, a);
      const qualifiers = (a.qualifiers || []).map(qualifierInfo).filter(Boolean);
      this.qualifiersByAssertion.set(a.id, qualifiers);
      for (const q of qualifiers) {
        add(this.byQualifier, `${q.predicate}|${q.key}`, { assertion: a, qualifier: q });
        if (q.id) add(this.byQualifierItem, q.id, { assertion: a, qualifier: q });
      }
    }
  }

  focusAssertions(focus) {
    if (!focus || typeof focus !== 'object') return [];
    if (focus.kind === 'entity') {
      const direct = this.byEntity.get(focus.id) || [];
      const tagged = (this.byQualifierItem.get(focus.id) || []).map((x) => x.assertion);
      return this.uniqueAssertions([...direct, ...tagged]);
    }
    if (focus.kind === 'source') return this.uniqueAssertions(this.bySource.get(focus.id) || []);
    if (focus.kind === 'qualifier')
      return this.uniqueAssertions(
        (this.byQualifier.get(`${focus.predicate}|${focus.key}`) || []).map((x) => x.assertion),
      );
    if (focus.kind === 'relation-value')
      return this.uniqueAssertions(this.byRelationValue.get(`${focus.relation}|${focus.key}`) || []);
    return [];
  }

  qualifiers(assertions) {
    const out = [];
    for (const a of assertions)
      for (const q of this.qualifiersByAssertion.get(a.id) || []) out.push({ assertion: a, qualifier: q });
    return out;
  }

  relationEdges(entityId, relationId) {
    return (this.entityEdges.get(entityId) || []).filter((edge) => edge.relationId === relationId);
  }

  relationAssertions(entityId, relationId) {
    return this.relationEdges(entityId, relationId).map((edge) => edge.assertion);
  }

  qualifierMatches(predicate, key) {
    return this.byQualifier.get(`${predicate}|${key}`) || [];
  }

  taggedMatches(id) {
    return this.byQualifierItem.get(id) || [];
  }

  uniqueAssertions(values) {
    return [...new Map(values.map((a) => [a.id, a])).values()];
  }
}

export { qualifierInfo };
