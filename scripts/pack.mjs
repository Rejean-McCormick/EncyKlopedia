import { loadPack, hash } from '../server/pack.mjs';
const pack = loadPack(process.argv[3]);
console.log(
  JSON.stringify(
    {
      valid: true,
      datasetRef: hash(pack),
      entities: pack.entities.length,
      assertions: pack.assertions.length,
      policies: pack.policies.length,
      synthetic: pack.synthetic,
    },
    null,
    2,
  ),
);
