# Konstellation — lecteur local Kristal v10 et diagnostic Manager alpha.14

**Statut : intégration expérimentale et optionnelle, non homologuée.** Ce changement
ne porte ni l'autorité épistémique du Framework ni les décisions de publication C2.

## Contrats et responsabilité

- **Framework 10.0.0-draft.3.2** : cadre de référence; la forme des états
  sémantiques reste `schema_version: "9.0"`. v10 ajoute l'hébergement et les
  surfaces de lecture. Un état v9 n'est donc pas une preuve de publication v10.
- **Manager alpha.14** : inventorie localement et peut fournir un rapport
  `kristal.manager-operational-assessment/0.2-candidate`, avec
  `operational_result`, `discovery.status`, `framework_state_verification.status`.
  Son export `kristal.manager-local-inventory/0.1-candidate`, **avec**
  `--verify-sources`, transporte ces trois statuts, et rien d'autre
  d'autoritatif. Le lecteur de Konstellation n'emploie pas ces valeurs
  comme droits d'accès, certificats ou validation métier.
- **Konstellation** : adapte ces observations à la vue `My Kristals`
  après filtrage d'accès explicite, puis lit et vérifie les octets
  consommés au moment d'ouvrir. Il ne fusionne pas les identités de Manager
  et d'un lecteur hébergé sans vérifications distinctes.
- **Arketype/Authoring Kit** : informations de classification et de lecture
  consultatives; aucun code ou parseur suggéré n'est chargé automatiquement.
- **Interaction Kernel v2.0-draft** : transporte des interactions et des
  références. Son lock Kristal 6.0.0 portable et son baseline v7 sont
  volontairement conservés. Aucun nouveau profil IK ni changement Daat
  n'est requis pour la lecture locale Konstellation.

## Installation Windows : Catho

Placez les dossiers extraits côte à côte :

```text
poste/
  Konstellation/
    Ouvrir_Kristal_Catho_v10.cmd
    examples/integrations/kristal-local-v10-catho.json
  A-Kristal-Catho/
    kristal.workspace.json
    state/state-snapshot.json
    build/v9/state-snapshot.json
    derived/catho-graph/
```

Avec Node.js **>=24.15** et npm installé, lancer
`Ouvrir_Kristal_Catho_v10.cmd`. Le lanceur existant installe les
dépendances au premier démarrage et construit l'interface; accès à
`http://127.0.0.1:4321`. Autre méthode explicite :

```powershell
$env:KONSTELLATION_BACKEND_CONFIG = 'C:\MonDossier\Konstellation\examples\integrations\kristal-local-v10-catho.json'
$env:KONSTELLATION_DEPLOYMENT_PROFILE = 'local'
$env:HOST = '127.0.0.1'
npm start
```

Ce profil lit un **workspace local explicitement sélectionné**. Le
lecteur n'effectue aucun scan automatique de tous les Kristals. Il
refuse le service en déploiement `public`, `lan` ou `shared`, ainsi
que les modes anonymous/public readonly.

## Ouvrir d'autres Kristals

L'adaptateur `kristal-local-v10` accepte :

- `directory` : emplacement du workspace spécifié par l'opérateur;
- `state` : chemin relatif de l'état (facultatif); sinon
  `state/state-snapshot.json`, ou `build/v9/state-snapshot.json` en repli;
- `readModel` optionnel et **explicitement configuré** :
  `type: node-edge-json/1`, `manifest`, `nodes`, `edges`.

Sans `readModel`, la vue présente la **topologie des membres déclarés**
de l'état v9; elle ne prétend pas décoder sémantiquement un type
d'artefact logique arbitraire. Un modèle dérivé exploitable exige un
manifeste `noncanonical=true`, `rebuildable=true`, et des empreintes
SHA-256 des entrées canoniques vérifiées. Les relations identitaires
candidates restent des assertions non validées.

Si l'inventaire Discovery diverge (p.ex. tailles périmées dans
Catho), la lecture générique n'est pas bloquée : la divergence
est exposée avec `discoveryStatus: stale`. Le profil Discovery ne peut
plus être utilisé comme preuve de fraîcheur. Le lecteur vérifie
séparément les chemins déclarés, le format de l'état et les
empreintes canoniques du graphe dérivé. Ces contrôles ne recalculent
pas le State Commitment JCS v9 : `canonicalCommitmentVerified=false`.

## Export Manager et permission distincte

Dans l'environnement Manager alpha.14 :

```powershell
python -m kristal_manager export C:\mes-kristals --verify-sources --output C:\prive\manager.json
```

Créer ensuite un fichier privé de type
`konstellation.manager-access-policy/0.1`, avec `state_ref`,
`state_commitment`, `allowed_principals` et `allowed_roles` explicites,
conformément à `examples/fleet/manager-access-policy.example.json`.
Configurer `KONSTELLATION_ENABLE_MY_KRISTALS=true`,
`KONSTELLATION_FLEET_EXPORT` et `KONSTELLATION_FLEET_POLICY`.
Sans politique : aucun inventaire Manager brut ne peut être affiché.
Les diagnostics Manager sont filtrés avant affichage, sans exposer
`issues`, chemins locaux ou données sources. Un élément d'inventaire
ne devient pas « openable » à partir du seul statut Manager.

## Limites et qualification

1. Lecteur dérivé et borné, pas décodeur universel de tous les types
   d'artefacts v9/v10 ni certificat Framework.
2. Aucune attestation de synchronisation, publication, activation,
   intégrité de signature C1/C2/C3, ni correction automatique de Discovery.
3. Le lecteur GitHub v10 demeure une vue technique de l'hébergement;
   l'adaptateur local v10 est un mécanisme différent et explicite.
4. Tests ciblés possibles avec le Node local; qualification complète
   nécessite Node >=24.15, dépendances, build, Svelte, Playwright et Windows.
5. Interaction Kernel et Daat n'ont pas été modifiés. Toute évolution
   IK exigerait une nouvelle négociation des profils et leur TCK.
