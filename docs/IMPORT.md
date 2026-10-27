# Import Kristal

## 1. Principe

L'import crée une **projection de lecture Konstellation**, jamais un nouveau canon.

## 2. Kristal v6 direct

Préférer l'adaptateur `kristal-state-v6` lorsque la source est v6.

```json
{
  "adapter": "kristal-state-v6",
  "state": "state.json",
  "requireIdentity": true
}
```

Le lecteur doit :

- valider le schéma ;
- vérifier l'identité si présente ;
- préserver les metadata v6 nécessaires ;
- projeter seulement les valeurs sans perte ;
- déclarer `importRecord.losses` ;
- ne jamais remplacer l'identité canonique.

## 3. Kristal-Kollection

Pour une collection contenant plusieurs dossiers `domains/Kristal-*`, utiliser l'adaptateur
`kristal-kollection-v1`. Il découvre le `*.kristal-state.json` du domaine sélectionné et active
un profil de compatibilité v6 **de lecture seulement** :

```json
{
  "adapter": "kristal-kollection-v1",
  "directory": "/chemin/vers/Kristal-Kollection",
  "kristal": "Biology"
}
```

Ce profil accepte les variantes observées dans la collection (par exemple
`content_hash.algorithm`, provenance absente et rôles de records additionnels). Les divergences
de schéma ou d'identité sont conservées dans `compatibilityWarnings`; elles ne deviennent jamais
une validation canonique. Les `assertion_id` dupliqués reçoivent des identifiants locaux uniques
et sont signalés dans `projectionWarnings`.

Le lecteur reconnaît les deux dispositions rencontrées dans la collection :
`knowledge-base/corpus/*.kristal-state.json` et `knowledge-base/*.kristal-state.json`.

## 4. Packs normalisés

Un pack normalisé reste utile comme cache/index local. Il doit porter suffisamment de contexte pour savoir :

- d'où il vient ;
- quelle version du canon il représente ;
- quelle policy a été appliquée si pertinente ;
- quelles pertes ont eu lieu.

## 5. Import ancien SES

L'import des Structured Epistemic States historiques reste un chemin de compatibilité. Toute conversion vers le modèle local doit être stricte et déclarer les structures non représentées.

## 6. Validation

Avant utilisation :

```bash
npm run pack:validate -- path/to/pack.json
```

Pour les imports :

```bash
npm run pack:import -- source.json mapping.json output.pack.json
```

## 7. Navigation après import

Une fois le pack chargé, le profiler analyse automatiquement sa structure. Aucune Lens spécifique n'est obligatoire pour obtenir la navigation générique.

Une Lens ou des `navigationHints` peuvent ensuite améliorer les labels, facettes ou recettes proposées.
