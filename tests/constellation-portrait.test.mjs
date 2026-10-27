import test from 'node:test';
import assert from 'node:assert/strict';
import { profileFamily, hasPortrait, portraitFor, orbitPreview, safePortraitUrl } from '../src/lib/constellation/profile.mjs';

test('fiches normalisées limitées aux types éligibles, sans faits inférés', () => {
  assert.equal(profileFamily('human')[1], 'Personne');
  assert.equal(profileFamily('location')[1], 'Lieu');
  assert.equal(hasPortrait({type:'relation'}), false);
  assert.equal(portraitFor({type:'person',label:'Hypatie', description:'Mathématicienne', aliases:['Hypatia']} ).description, 'Mathématicienne');
  assert.deepEqual(portraitFor({type:'place',label:'Lyon',period:'Antiquité'}).fields, [{name:'Période',value:'Antiquité'}]);
  assert.equal(portraitFor({type:'group',label:'Groupe'}), null);
});
test('portraits issus uniquement de chemins image locaux sûrs', () => {
  assert.equal(safePortraitUrl('https://example.com/image.jpg'), null);
  assert.equal(safePortraitUrl('//attacker.test/x.svg'), null);
  assert.equal(safePortraitUrl('/a/../private.png'), null);
  assert.equal(safePortraitUrl('javascript:alert(1)'), null);
  assert.equal(safePortraitUrl('./portraits/figure.png'), './portraits/figure.png');
});
test('aperçu limité à 6 satellites et borné au viewport', () => {
  const nodes=Array.from({length:12},(_,i)=>({id:`n${i}`,label:`N${i}`}));
  for(const anchor of [{x:20,y:20},{x:990,y:600},{x:400,y:250}]) {
    const out=orbitPreview(nodes,anchor,1000,620);
    assert.equal(out.length,6);
    assert(out.every(n=>n.x>=70&&n.x<=930&&n.y>=45&&n.y<=575));
  }
  assert.equal(nodes.length,12);
});

test('protection contre les chemins encodés, protocoles et extensions exécutables', () => {
  for(const url of ['/%2e%2e/admin.jpg','./images/%252e%252e/private.jpg','./images/%5c/private.png',
    './media/picture.svg','//example.org/a.png','https://site.com/photo.jpg','./pic.png?tracking=1'])
    assert.equal(safePortraitUrl(url),null,url);
  assert.equal(safePortraitUrl('/img/marie.webp'),'/img/marie.webp');
});
test('fiches typées sans valeurs fabriquées', () => {
  const person=portraitFor({type:'person',label:'Marie',birthDate:'1900',occupation:'Autrice'});
  assert.deepEqual(person.fields.slice(0,2),[{name:'Naissance',value:'1900'},{name:'Activité',value:'Autrice'}]);
  const place=portraitFor({type:'place',label:'Montreal',country:'Canada'});
  assert.equal(place.fields[0].value,'Canada');
  assert.equal(place.fields.some(f=>f.name==='Naissance'),false);
});
test('prépositionnement du deuxième anneau évite les bulles existantes', () => {
  const items=Array.from({length:6},(_,i)=>({id:'sub'+i,label:'Sub '+i}));
  for (const [w,h] of [[1000,620],[760,470]]) {
    const anchor={x:w*.72,y:h*.5};
    const obstacles=Array.from({length:12},(_,i)=>({x:w/2+w*.35*Math.cos(i*Math.PI/6),y:h/2+h*.35*Math.sin(i*Math.PI/6),r:26}));
    const points=orbitPreview(items,anchor,w,h,6,obstacles);
    assert.equal(points.length,6);
    assert(points.every(p=>p.x>=70&&p.x<=w-70&&p.y>=45&&p.y<=h-60));
    for(let i=0;i<points.length;i++) for(let j=i+1;j<points.length;j++)
      assert(Math.hypot(points[i].x-points[j].x,points[i].y-points[j].y)>=68);
    assert.deepEqual(items.map(n=>n.id),['sub0','sub1','sub2','sub3','sub4','sub5']);
  }
});
