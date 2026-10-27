# Adaptateur GitHub Kristal v10 — navigation locale vérifiée

## Objet

`kristal-github-collection-v10` permet à Konstellation de naviguer dans la
**topologie opérationnelle** des surfaces GitHub v10 draft.3 préparées par le
Local Kit et synchronisées par Kristal Manager. Il ne fusionne pas Konstellation
avec Kompiler et ne remplace pas son lecteur direct `kristal_state` v6.

Source à fournir : copie locale complète et fiable du dépôt de collection,
avec `kristals/index.json` et, pour chaque slug sélectionné :

- `kristals/<slug>/.kristal/sync-manifest.json` ;
- `AI_MANIFEST.json`, `ai/INDEX.json`, `state/state-snapshot.json` ;
- tous les fichiers du manifeste de synchronisation (tailles et empreintes).

Le lecteur ne récupère rien depuis GitHub : la synchronisation relève du Manager.

## Configuration

Exemple dans `examples/integrations/kristal-github-v10.json`. `directory` est
résolu relativement au **fichier JSON de configuration**, pas au dossier d’exécution.
Remplacer sa valeur par le chemin relatif ou absolu du dépôt local (Windows :
`C:/mycode/Kristal/mon-depot-github`). `kristal` est le slug exact annoncé par
`kristals/index.json`, pas le nom d’un fichier arbitraire.

Dans PowerShell, après installation des dépendances du dépôt Konstellation :

```powershell
$env:KONSTELLATION_BACKEND_CONFIG = "C:\mycode\Konstellation\examples\integrations\kristal-github-v10.json"
npm start
```

L’API `/api/kristals` et le sélecteur de l’interface exposent les entrées de
l’index. Chaque sélection déclenche une vérification des fichiers correspondants.
Une entrée mal synchronisée échoue plutôt que d’exposer une topologie obsolète.

## Vérifications et limites

- Contrôle du format et digest JCS de l’index de collection, de l’ordre et des slugs.
- Contrôle du manifeste `.kristal/sync-manifest.json` et de son `surface_digest`
  selon la projection `kristal.github-read-surface/1.0` du Framework.
- Relecture des octets et contrôle SHA-256/tailles de chaque fichier, avec
  budgets `maxFiles` et `maxBytes`.
- Refus des fichiers non répertoriés, liens symboliques, traversées `..` et
  divergences `AI_MANIFEST` / `ai/INDEX` / Snapshot v9.
- Contrôle des déclarations `state_ref` et `logical_commitment` **entre fichiers**.
  Ceci n’équivaut **pas** à un recalcul indépendant du State Commitment v9, ni à
  une vérification de signatures ou d’autorité.
- Politique de lecture normalisée réservée à la navigation technique, sans
  assertions de domaine ni inférence « absence = faux ».
- Des fichiers v9 `canonical_content` peuvent être de n’importe quel type
  logique : aucune conversion générique sans perte vers `kristal_state` v6
  n’est revendiquée.

## Modèle de la vue

L’état v9 est représenté par une entité `hosted_state` ; les `members[]`
forment des entités `logical_artifact` et les fichiers vérifiés des entités
`hosted_file`. Les relations `has_member` et `lists_file` ne représentent que
les **déclarations et indexations opérationnelles** du snapshot et du manifeste.
Les assertions techniques ont `status=unspecified`,
`validationStatus=not_evaluated`, `authority=authority:unspecified`.
Le pack est `synthetic=true`, `integration.viewKind=derived-hosting-navigation`.

**Invariants :** `READ SURFACE != SEMANTIC STATE`,
`SYNC != PUBLICATION != ACTIVATION`, `COLLECTION INDEX != AUTHORITY`.

## Qualification

Exécuter `node --test tests/kristal-v10.test.mjs` (test autonome) puis,
sous Node >=24.15 avec `node_modules` : `npm test`, `npm run test:ui`,
`npm run build` et le gate de release habituel. Les tests unitaires ne
valident pas à eux seuls l’interface sous Windows ni Playwright.
