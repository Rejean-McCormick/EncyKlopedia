# Validation v0.5

## Portée

La v0.5 ajoute une projection de navigation bornée nommée **Constellation**. Elle n'altère ni QuerySpec, ni Reader Policy, ni les assertions du pack. Le Query Service choisit et classe les satellites; le frontend Svelte ne fait que rendre le DTO de constellation et gérer le chemin de navigation.

## Contrats et invariants

- budget de satellites : entier de 3 à 25;
- même `context` que le reste du Query Service;
- toutes les assertions utilisées pour une constellation proviennent de `scope(context)`, donc après ACL et Reader Policy;
- un groupe de Lens est une construction de navigation, jamais une entité du corpus;
- les qualificatifs sont indexés comme points d'accès mais ne deviennent pas des assertions;
- ordre et score déterministes pour les mêmes données, politique, Lens et limite;
- aucun LLM, embedding ou appel distant pour la saillance;
- les anciennes explorations `view: graph` restent acceptées et sont restaurées dans la vue Constellation.

## Vérifications réalisées dans l'environnement de génération

- `node --check` : modules de navigation, moteur, serveur et tests modifiés;
- tests unitaires du nouveau projecteur avec un stub local d'Ajv : 2/2 passés;
- essai du projecteur sur le pack Théophile fourni : Augustin produit les groupes Pensée, Œuvres et sources, Positions documentées, Genres documentaires et Repères chronologiques; le thème grâce mène aux auteurs, positions et relations documentées associées;
- validation JSON Schema 2020-12 avec `jsonschema` : schémas valides, trois Lens d’exemple valides, état d’exploration d’exemple valide et réponse réelle du projecteur Théophile valide contre `constellation-response.schema.json`.

La suite `npm run check` doit être rejouée sur l'installation Node 24 du dépôt après application de l'overlay; les dépendances npm ne sont pas embarquées dans le snapshot de travail utilisé ici.
