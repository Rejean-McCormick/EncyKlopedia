# Qualification indépendante du Kit v4.0.0-draft.4 — Framework v11 draft.4

**Historique :** les validations précédemment exécutées sur le snapshot draft.2 et ses fixtures de référence restent documentées. Un test de qualification doit être relancé avec les artefacts pinned disponibles avant toute conclusion concernant draft.3.

**Portée :** il s'agit d'une qualification locale en lecture seule utilisant les **schémas et outils réels** de `Kristal Framework 11.0.0-draft.4`, ainsi que, facultativement, l'Integration Pack `0.3.0-alpha.1`. Ce n'est ni une publication GitHub, ni une certification de tous les Kristals historiques.

## Contrat partagé et version bloquée

`contracts/v11-framework-pin.json` contient les mêmes empreintes SHA-256 que le fichier homologue de l'Integration Pack. Le Kit refuse si la version, un schéma ou un outil normatif référencé a changé. Toute mise à niveau Framework doit être examinée, testée et repinnée explicitement dans **les deux dépôts**.

Les commandes courantes (`check-v11`, `coverage-v11`, `build-v9`) restent autonomes en bibliothèque standard et utilisent le validateur local. La commande de qualification indépendante utilise en plus `jsonschema` comme le Framework. Les entrées restent locales ; aucun téléchargement ni modification des engagements.

## Exécution

Depuis le dépôt **complet** Authoring Kit (pas une simple copie de `tools/kristal.py` dans un Kristal) :

```bash
python -m pip install jsonschema
python tools/kristal.py qualify-v11 ./examples/demo-semantic-v11 \
  --framework ../kristal-11.0.0-draft.4 \
  --integration-pack ../Kristal-Integration-Pack-0.3.0-alpha.1 \
  --locales fr,fr-CA
```

Ou avec un autre projet v11 activé :

```bash
python scripts/qualify_framework_v11.py --project ../MonKristal \
  --framework ../kristal-11.0.0-draft.4
```

## Vérifications

1. Empreintes exactes et version déclarée de Framework v11 et des validateurs concernés.
2. Exemples de référence et miroirs TCK du Framework, puis validation du graphe actif et de ses KQ/KP/KA/KS à l'aide du **vrai validateur Framework**.
3. Audit des dictionnaires, intégrité SHA-256, provenance Wikidata et correspondances exactes approuvées, avec les outils Framework.
4. Calcul indépendant de la complétude du même graphe et comparaison JSON exacte des rapports produits par le Kit et le Framework (direct, repli, manquant).
5. Avec `--integration-pack` : égalité du pin, contrôle du consommateur v11, puis **égalité du rapport de complétude** entre Kit, Framework et Pack.
6. Empreintes du graphe et du catalogue incluses dans le résultat, pour prouver quels fichiers ont été lus.

Le rapport de qualification n'est pas une autorisation de publier, de convertir un référent incertain, ni d'affirmer la complétude d'un Kristal historique contenant encore des mots à résoudre.

## Limites et migration

La conversion `apply-v11-plan` reste bornée aux **graphes déjà structurés en v11** où seules certaines identités doivent être résolues, avec chemin d'identité approuvé, revue et preuve. Un ancien corpus arbitraire ne peut pas être converti par simple correspondance de mots. L'écriture de plusieurs fichiers est actuellement protégée par rollback sur exception, mais **pas** encore par un journal crash-safe ; ne pas qualifier cette fonction pour des migrations critiques avant d'avoir ajouté ces garanties.

La qualification est à répéter pour tout nouveau Framework, nouveau Pack, nouveaux dictionnaires, et toute évolution d'une politique de correspondances.

## Provenance de la livraison

Le ZIP `authkit.zip` fourni le 16 octobre 2026 ne contient que 14 fichiers de build v9, sans sources du Kit. La présente version est fondée sur le snapshot complet `Kristal-Authoring-Kit-4.0.0-draft.1(1).zip`, avec ajout sans écrasement des 13 fichiers de build absents, et conservation de l'artefact déjà identique. Les autres contenus d'origine sont conservés.
