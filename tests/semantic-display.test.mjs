import test from 'node:test';
import assert from 'node:assert/strict';
import { semanticLabel, readableCode, readableStatus, readableNodeLabel,
  orientationScore, rankOrientation } from '../src/lib/semantic-display.mjs';

test('known Wikidata properties receive French labels without changing the source identifier', () => {
  assert.equal(semanticLabel('P138'), 'Nommé d’après');
  assert.equal(semanticLabel('P50'), 'Auteur');
  assert.equal(semanticLabel('P50', {configured:'Auteur (P50)'}), 'Auteur');
  assert.equal(semanticLabel('P9745'), 'Propriété Wikidata P9745 (libellé indisponible)');
  assert.equal(semanticLabel('P138', {configured:'Nommé en hommage à'}), 'Nommé en hommage à');
  assert.equal(readableCode('Q7251'), 'Élément Wikidata Q7251 (libellé indisponible)');
});
test('Catho predicates use grounded, non-assertive source labels', () => {
  assert.equal(semanticLabel('academicien_sur_liste_publiee'),
    'Source attestant une inscription sur une liste d’académiciens');
  assert.equal(semanticLabel('saintete_reconnue'), 'Source relative à la sainteté reconnue');
  assert.equal(semanticLabel('pontificat_recense'), 'Pontificat recensé');
  assert.equal(semanticLabel('custom_test_type'), 'Custom test type');
});
test('status codes and open-research hypothesis prefixes become readable without altering truth claims', () => {
  assert.equal(readableStatus('not_evaluated'), 'Non évalué');
  assert.equal(readableStatus('read_only_local_projection'), 'Projection locale en lecture seule');
  assert.equal(readableNodeLabel('wikidata_identity · Albert le Grand','unconfirmed_research_claim'),
    'Identité Wikidata proposée · Albert le Grand');
  assert.equal(readableNodeLabel('wikidata_identity · Albert le Grand','catho_person'),
    'wikidata_identity · Albert le Grand');
});
test('Astrolabe matches word boundaries: aquin does not match Joaquín', () => {
  const entities=[
    {id:'a',label:'Thomas d’Aquin',type:'catho_person'},
    {id:'b',label:'La postérité de Joaquín de Fiore',type:'wikidata_work'},
    {id:'c',label:'Thomas Aquinas',type:'wikidata_item'},
  ];
  assert.equal(orientationScore(entities[1],'aquin'),0);
  assert(orientationScore(entities[0],'aquin')>0);
  assert.deepEqual(rankOrientation(entities,'aquin').map(x=>x.entity.id),['a','c']);
});

test('search diversity does not merge duplicate IDs and respects preferred category', () => {
  const entities=[
    {id:'work',label:'Thomas d’Aquin',type:'wikidata_work'},
    {id:'person',label:'Thomas d’Aquin',type:'catho_person'},
    {id:'different',label:'De Thomas d’Aquin à la scolastique',type:'wikidata_work'},
  ];
  const ranked=rankOrientation(entities,'aquin',16,'catho_person');
  assert.deepEqual(ranked.map(x=>x.entity.id),['person','different','work']);
  assert.equal(ranked.length,3);
});
