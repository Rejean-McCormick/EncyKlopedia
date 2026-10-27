import fs from 'node:fs';
import { ROOT } from '../server/contracts.mjs';
const registry = JSON.parse(fs.readFileSync(`${ROOT}/examples/registry.json`));
const entities = [],
  assertions = [],
  sources = [
    {
      id: 'demo:catalogue',
      title: 'Catalogue de démonstration Konstellation',
      description:
        'Exemples illustratifs et relations synthétiques. Ce jeu ne constitue pas un corpus historique validé.',
    },
    {
      id: 'demo:research',
      title: 'Carnet de recherche fictif',
      description: 'Assertions hypothétiques et divergentes pour tester les politiques de lecture.',
    },
  ];
const entity = (id, type, label, description = '') => {
  entities.push({ id, type, label, description });
  return id;
};
const philosophy = entity('demo:philosophy', 'concept', 'Philosophie'),
  theology = entity('demo:theology', 'concept', 'Théologie'),
  science = entity('demo:science', 'concept', 'Sciences'),
  literature = entity('demo:literature', 'concept', 'Littérature');
for (const [id, label] of [
  ['platonism', 'Platonisme'],
  ['scholastic', 'Scolastique'],
  ['stoic', 'Stoïcisme'],
  ['christian', 'Tradition chrétienne'],
])
  entity('demo:' + id, 'concept', label);
for (const [id, label] of [
  ['africa', 'Afrique du Nord'],
  ['italy', 'Italie'],
  ['greece', 'Grèce'],
  ['france', 'France'],
  ['egypt', 'Égypte'],
])
  entity('demo:' + id, 'place', label);
let counter = 0;
function add(subject, relation, value, extra = {}) {
  const a = {
    id: 'demo:a' + String(++counter).padStart(5, '0'),
    subject,
    relation,
    value,
    status: 'sourced',
    certainty: 'medium',
    validationStatus: 'not_evaluated',
    validatedAs: 'sourced_claim',
    authority: 'authority:demo',
    scope: { domain: 'demonstration' },
    sourceRefs: ['demo:catalogue'],
    ...extra,
  };
  assertions.push(a);
  return a;
}
const people = [
  ['Augustin d’Hippone', 354, 430, 'africa', 'platonism'],
  ['Hypatie d’Alexandrie', 360, 415, 'egypt', 'platonism'],
  ['Boèce', 480, 524, 'italy', 'platonism'],
  ['Thomas d’Aquin', 1225, 1274, 'italy', 'scholastic'],
  ['Hildegarde de Bingen', 1098, 1179, 'france', null],
  ['Avicenne', 980, 1037, 'greece', null],
  ['Christine de Pizan', 1364, 1430, 'france', null],
  ['Érasme', 1466, 1536, 'italy', null],
  ['Simone Weil', 1909, 1943, 'france', null],
  ['Émilie du Châtelet', 1706, 1749, 'france', null],
  ['Plotin', 205, 270, 'egypt', 'platonism'],
  ['Marc Aurèle', 121, 180, 'italy', 'stoic'],
];
for (let i = 0; i < people.length; i++) {
  const [label, start, end, place, movement] = people[i],
    p = entity(
      `demo:p${String(i).padStart(3, '0')}`,
      'human',
      label,
      'Notice illustrative · assertions de démonstration',
    );
  add(p, 'field_of_work', i === 6 ? literature : philosophy);
  if (i % 3 === 0) add(p, 'field_of_work', theology);
  if (i === 1 || i === 9) add(p, 'field_of_work', science);
  add(
    p,
    'lifespan',
    { startMin: start, startMax: start, endMin: end, endMax: end },
    { ruleRef: 'demo:interval-v1', derivedFrom: ['demo:catalogue'] },
  );
  add(p, 'birth_place', 'demo:' + place);
  add(p, 'citizenship', 'demo:' + place);
  if (movement) add(p, 'movement', 'demo:' + movement);
  if (i === 0 || i === 3 || i === 4) add(p, 'religious_tradition', 'demo:christian');
  const titles =
    i === 0
      ? ['Les Confessions', 'La Cité de Dieu']
      : i === 2
        ? ['Consolation de la philosophie']
        : i === 3
          ? ['Somme théologique']
          : ['Œuvre de démonstration ' + (i + 1)];
  for (let j = 0; j < titles.length; j++) {
    const w = entity(
      `demo:w${String(i).padStart(3, '0')}-${j}`,
      'work',
      titles[j],
      'Attribution illustrative pour tester le parcours',
    );
    add(w, 'author', p);
  }
}
const disputed = add('demo:p000', 'movement', 'demo:stoic', {
  status: 'disputed',
  certainty: 'low',
  sourceRefs: ['demo:research'],
});
const established = assertions.find(
  (a) => a.subject === 'demo:p000' && a.relation === 'movement' && a.value === 'demo:platonism',
);
established.conflictsWith = [disputed.id];
disputed.conflictsWith = [established.id];
// More than one page, deliberately synthetic people and works.
for (let i = 0; i < 120; i++) {
  const p = entity(
    'demo:s' + String(i).padStart(3, '0'),
    'human',
    'Chercheur fictif ' + String(i + 1).padStart(3, '0'),
    'Entité synthétique · test de sélection complète',
  );
  add(p, 'field_of_work', i % 2 ? science : philosophy);
  const start = 200 + i * 8;
  add(
    p,
    'lifespan',
    {
      startMin: start,
      startMax: start,
      endMin: i % 11 ? start + 65 : null,
      endMax: i % 11 ? start + 65 : null,
    },
    { ruleRef: 'demo:interval-v1', derivedFrom: ['demo:catalogue'] },
  );
  add(p, 'birth_place', 'demo:' + ['africa', 'italy', 'greece', 'france', 'egypt'][i % 5]);
  if (i % 3) add(p, 'movement', 'demo:platonism');
  const w = entity(
    'demo:sw' + String(i).padStart(3, '0'),
    'work',
    'Étude synthétique ' + String(i + 1).padStart(3, '0'),
    'Œuvre générée pour les tests de navigation',
  );
  add(w, 'author', p);
}
const policy = (id, label, statuses, description) => ({
  id,
  label,
  description,
  profile: 'konstellation.normalized-reader.v1',
  showLabels: true,
  statuses,
  certainties: ['*'],
  validationStatuses: ['*'],
  validatedAs: ['*'],
  authorities: ['authority:demo'],
  requireSources: true,
});
const pack = {
  schemaVersion: '0.3',
  title: 'Atlas des idées',
  description: 'Personnes, œuvres et relations · démonstration locale',
  synthetic: true,
  registry,
  entities,
  assertions,
  sources,
  policies: [
    policy(
      'demo:documented',
      'Assertions sourcées',
      ['sourced', 'reviewed', 'validated'],
      'Affiche les assertions sourcées de la démonstration. Ne signifie pas « validé ».',
    ),
    policy(
      'demo:research',
      'Recherche avec divergences',
      ['sourced', 'reviewed', 'validated', 'hypothesis', 'claimed', 'disputed'],
      'Inclut les hypothèses et divergences en conservant leurs statuts.',
    ),
  ],
};
fs.writeFileSync(`${ROOT}/data/demo.pack.json`, JSON.stringify(pack, null, 2) + '\n');
