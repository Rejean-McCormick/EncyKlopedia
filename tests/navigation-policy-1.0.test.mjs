import test from 'node:test';
import assert from 'node:assert/strict';
import { Engine } from '../server/engine.mjs';

const policy = (id, statuses) => ({
  id, label: id, description: id, profile: 'konstellation.normalized-reader.v1', showLabels: true,
  statuses, certainties: ['*'], validationStatuses: ['*'], validatedAs: ['*'], authorities: ['*'], requireSources: false,
});

function fixture() {
  return {
    schemaVersion: '0.3', title: 'Policy navigation', description: 'Policy-scoped navigation fixture', synthetic: true,
    registry: {
      schemaVersion: '0.2', registryRef: 'policy-nav', entityTypes: ['node'],
      relations: [
        { id: 'related', label: { fr: 'lié à', en: 'related to' }, domain: ['node'], range: 'node', valueKind: 'entity', operators: ['exists','missing_in_view','in','none_of'] },
        { id: 'hidden_date', label: { fr: 'date', en: 'date' }, domain: ['node'], range: 'interval', valueKind: 'interval', operators: ['exists','missing_in_view','overlaps'] },
      ],
    },
    entities: [{ id: 'a', type: 'node', label: 'A' }, { id: 'b', type: 'node', label: 'B' }, { id: 'c', type: 'node', label: 'C hidden' }],
    sources: [],
    assertions: [
      { id:'visible', subject:'a', relation:'related', value:'b', status:'sourced', certainty:'known', validationStatus:'reviewed', validatedAs:'claim', authority:'authority:test', scope:{domain:'test'}, sourceRefs:[] },
      { id:'hidden-temporal', subject:'c', relation:'hidden_date', value:{startMin:1900,startMax:1900,endMin:1900,endMax:1900,calendar:'proleptic-gregorian-astronomical'}, ruleRef:'test:interval', derivedFrom:[], status:'disputed', certainty:'known', validationStatus:'reviewed', validatedAs:'claim', authority:'authority:test', scope:{domain:'test'}, sourceRefs:[] },
    ],
    policies: [policy('documented',['sourced']), policy('research',['*'])],
  };
}

const lenses = [{ schemaVersion:'0.2', id:'type:node', label:{fr:'Node',en:'Node'}, rootType:'node', facets:[{relation:'hidden_date',widget:'year-range'}], pivots:[], constellation:{defaultSatelliteCount:8,groups:[{id:'hidden-time',label:{fr:'Temps secret',en:'Secret time'},priority:1,source:{kind:'relations',ids:['hidden_date']}}]} }];
function query(engine, readerPolicyRef) {
  return { schemaVersion:'0.2', context:{...engine.baseContext,readerPolicyRef}, selection:{entityType:'node',filters:[],links:[]}, order:'entity_id_asc', pageSize:24 };
}

test('hidden-only structural relations cannot leak through navigation affordances', () => {
  const engine = new Engine(fixture());
  const refs = [...engine.policies.keys()];
  const documented = refs.find((ref) => engine.policies.get(ref).id === 'documented');
  const research = refs.find((ref) => engine.policies.get(ref).id === 'research');
  const hiddenPlan = engine.navigationPlan({ query:query(engine,documented), lensRef:'type:node' }, lenses);
  const fullPlan = engine.navigationPlan({ query:query(engine,research), lensRef:'type:node' }, lenses);
  assert(!hiddenPlan.views.some((view) => view.id === 'timeline'));
  assert(fullPlan.views.some((view) => view.id === 'timeline'));
  assert(!hiddenPlan.profile.affordances.temporal);
});

test('policy-scoped navigation suppresses presentation hints that could reveal hidden structure', () => {
  const pack = fixture();
  pack.navigationHints = {
    schemaVersion: '1.0',
    preferredRecipes: ['timeline'],
    recipeLabels: { timeline: 'Chronologie du projet SECRET' },
    affordances: { temporal: { score: 1, reason: 'structure sensible' } },
    relationAffordances: { hidden_date: ['temporal'] },
  };
  const engine = new Engine(pack);
  const refs = [...engine.policies.keys()];
  const documented = refs.find((ref) => engine.policies.get(ref).id === 'documented');
  const hiddenPlan = engine.navigationPlan({ query:query(engine,documented), lensRef:'type:node' }, lenses);
  assert(!hiddenPlan.views.some((view) => view.id === 'timeline'));
  assert(!JSON.stringify(hiddenPlan).includes('SECRET'));
  assert(!JSON.stringify(hiddenPlan).includes('structure sensible'));
});


test('hidden entity identifiers validate exactly like unknown identifiers', () => {
  const engine = new Engine(fixture());
  const refs = [...engine.policies.keys()];
  const documented = refs.find((ref) => engine.policies.get(ref).id === 'documented');
  const hidden = query(engine, documented); hidden.selection.ids = ['c'];
  const missing = query(engine, documented); missing.selection.ids = ['does-not-exist'];
  let hiddenError, missingError;
  try { engine.check(hidden); } catch (error) { hiddenError = error; }
  try { engine.check(missing); } catch (error) { missingError = error; }
  assert(hiddenError); assert(missingError);
  assert.equal(hiddenError.code, missingError.code);
  assert.equal(hiddenError.message, missingError.message);
});


test('bootstrap registry and Lens metadata are policy-scoped', () => {
  const engine = new Engine(fixture());
  const refs = [...engine.policies.keys()];
  const documented = refs.find((ref) => engine.policies.get(ref).id === 'documented');
  const research = refs.find((ref) => engine.policies.get(ref).id === 'research');
  const restricted = engine.bootstrap(lenses, engine.context(documented));
  const full = engine.bootstrap(lenses, engine.context(research));
  assert(!restricted.registry.relations.some((relation) => relation.id === 'hidden_date'));
  assert(!restricted.lenses[0].facets.some((facet) => facet.relation === 'hidden_date'));
  assert(!JSON.stringify(restricted.lenses).includes('Temps secret'));
  assert(full.registry.relations.some((relation) => relation.id === 'hidden_date'));
  assert(full.lenses[0].facets.some((facet) => facet.relation === 'hidden_date'));
});
