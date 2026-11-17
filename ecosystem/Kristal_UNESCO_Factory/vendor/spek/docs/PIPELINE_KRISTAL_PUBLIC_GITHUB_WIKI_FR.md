# Du Kristal canonique à GitHub Wiki — format et responsabilités

Ce document décrit la **destination de publication des Kristals** dans `Rejean-McCormick/kristal-public`. Il ne faut pas la confondre avec le **Wiki de documentation du dépôt Spek** (`Spek.wiki`).

## Contrats et sorties déjà identifiés dans les archives de code

- Canon local : `C:\mycode\Kristal\locals\<Kristal>` ; aucune écriture canonique par l'atelier Spek.
- Manager : contrôle du choix des assertions, des références d'état et des autorisations C1/C2/C3.
- Plan de transmission : `kristal.wiki-editorial-plan/1.0` et collection indexée C3, préparés à partir de faits explicitement sélectionnés.
- SemantiK Architect : `semantik.kristal-v6.communication-projection/1.0` ; moteur GF/PGF / RuntimeSet pour produire des expressions bornées dans la langue sélectionnée. L'atelier ne certifie pas ce RuntimeSet et n'exécute pas automatiquement SemantiK depuis un état brut.
- Adaptateur éditorial : `kristal.layout-article-source/0.1` (sections et slots explicites) et `kristal.layout-realizations/0.1` (phrases par clé et langue, provenance SemantiK).
- Spek : vérifie types et cardinalités de layout, provenance déclarée, puis assemble les brouillons Wiki privés.
- Destinations GitHub : dépôt `Rejean-McCormick/kristal-public` pour les données publiques approuvées, et dépôt Git séparé `Rejean-McCormick/kristal-public.wiki.git` pour les pages natives Wiki.

## Organisation d'un brouillon par collection

```text
private-wiki-draft/
├── Home.md
├── _Sidebar.md
├── Kristal-ai.md
├── Kristal-accounting.md
├── Kristal-aerospace.md
├── ...
└── manifest.json
```

Le format du manifeste de Spek est `spek.wiki-draft/1.0` pour une page ou collection selon le pipeline. Les pages doivent correspondre **exactement aux slugs canoniques sans préfixe** (`agriculture`, `aerospace`, etc.). Le préfixe `Kristal-` dans les **noms de pages** est une convention de présentation, pas une partie du slug.

## Étape présente vs étape à venir

**Fonctionnel dans cette version Spek :** 127 propositions IA consultables, cinq revues structurelles, inspection privée en HTML des assertions explicitement réparties, 27 layouts typés (8 historiques + 19 spécialisés), compilation à partir d'articles/realizations explicites et génération de brouillons GitHub Wiki privés.

**Ne fait pas partie de ce ZIP Spek :** l'installation du code SemantiK Architect et de son RuntimeSet, la sélection humaine/éditoriale finale de chaque assertion, la vérification C1/C2/C3 en ligne, la création/activation de `kristal-public.wiki.git`, l'authentification GitHub, un Git push ou une publication effective.

**Le passage à la publication ne peut pas être inféré par Spek.** Les sources contenues dans l'inspection privée ne sont pas une autorisation et ne doivent pas être copiées directement dans les pages publiques. La provenance et les attestations doivent être vérifiées indépendamment.
