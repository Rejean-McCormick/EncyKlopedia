# Backup / restore — Konstellation 1.0

Konstellation est principalement un navigateur dérivé. Le backup doit donc protéger en priorité **les entrées canoniques et la configuration de déploiement**, pas les projections reconstructibles.

## Ce qui doit être sauvegardé

| Élément | Priorité | Remarque |
|---|---:|---|
| Kristal canonique / `kristal_state` | critique | source de vérité |
| sources/evidence référencées si locales | critique | conserver identité et intégrité |
| Lens et Reader Policies déployées | critique | font partie du comportement observable |
| configuration non secrète | haute | profil, chemins, budgets, allowlists |
| secrets auth/cursor | critique mais séparé | sauvegarde dans un secret manager, jamais dans l'archive applicative |
| `package-lock.json`, source release, manifest, SBOM | haute | reproductibilité et rollback |
| logs/audit selon politique de rétention | variable | respecter confidentialité et réglementation |
| caches, result sets, NavigationPlans, projections | aucune | reconstructibles ; ne pas sauvegarder comme vérité |

## Format recommandé

Une sauvegarde doit être atomique ou référencer un snapshot cohérent :

```text
backup/<timestamp>/
  kristal/
  lenses/
  policies/
  config/
  release/
    package-lock.json
    RELEASE-MANIFEST.json
    SBOM.cdx.json
    version.json
  checksums.sha256
```

Les secrets sont référencés par identifiant/version dans le manifest de backup, mais stockés séparément.

## Procédure de backup

1. identifier la version et le build via `/api/version` ;
2. snapshotter le Kristal canonique et les fichiers Lens/Policy de manière cohérente ;
3. inclure les artefacts de release reproductibles ;
4. calculer SHA-256 de chaque fichier ;
5. chiffrer au repos selon le profil de déploiement ;
6. copier vers un emplacement indépendant ;
7. vérifier automatiquement l'archive après écriture ;
8. enregistrer date, propriétaire, rétention et version de schéma.

Pour un Kristal modifié en continu, utiliser le mécanisme transactionnel/snapshot fourni par son stockage amont. Ne jamais copier partiellement un état en cours d'écriture si cela peut rompre ses invariants.

## Procédure de restore

1. isoler une nouvelle instance ;
2. restaurer la **même release** ou une release explicitement compatible ;
3. vérifier les checksums avant chargement ;
4. restaurer Kristal, Lens, Reader Policies et configuration ;
5. injecter les secrets depuis le secret manager ;
6. démarrer sans trafic ;
7. attendre `/api/ready` vert ;
8. comparer `/api/version` et l'identité attendue ;
9. exécuter smoke tests : liste, entity, policy, plan, projection, evidence ;
10. pour un environnement partagé, tester au moins un principal autorisé et un principal restreint ;
11. ouvrir progressivement le trafic ;
12. ne jamais restaurer les caches/projections comme état canonique.

## Restore après changement de version

Si le backup provient d'une version antérieure :

- appliquer les migrations contractuelles explicites ;
- conserver le backup original immuable ;
- produire un rapport de migration/loss report ;
- valider le Kristal avant ouverture ;
- ne jamais modifier silencieusement une Reader Policy ou une sémantique d'actionability.

## Objectifs RPO/RTO

Konstellation ne fixe pas une valeur universelle. Chaque déploiement doit déclarer :

- **RPO** : perte de données canoniques acceptable ;
- **RTO** : délai acceptable avant restauration du service ;
- fréquence et rétention des backups ;
- fréquence des exercices de restore.

Pour un service critique, un restore test automatisé périodique est requis ; une sauvegarde jamais restaurée n'est pas considérée comme vérifiée.

## Test de restauration

Au minimum à chaque changement majeur de stockage ou avant une release critique :

```text
backup -> environnement isolé -> checksum -> startup -> ready
       -> policy smoke -> navigation smoke -> version check
```

Le test doit échouer si le Kristal, une policy, un secret requis ou un artefact de release manque.

## Données à ne pas recopier dans les tickets/incidents

Ne pas joindre de tokens, sources sensibles, assertions masquées, dumps complets de Kristal ou clés de cursor. Utiliser requestId, hash, identifiants non sensibles et extraits minimaux autorisés.
