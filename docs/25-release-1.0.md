# Critères de release Konstellation 1.0

Konstellation n'est déclaré production-ready que pour un profil de déploiement donné lorsque **tous les gates applicables** sont verts.

## Gates

| Gate | Condition |
|---|---|
| Architecture | invariants des docs 00, 04 et 16 couverts par tests |
| Contrats | schémas publics versionnés, examples valides, migration documentée |
| Renderers | renderers prioritaires natifs, accessibles et bornés |
| Golden corpus | Math, HumanBody, HistoryTech, ScolQc, HospitalOps, Power, Catho + generic passent |
| Build | `npm ci`, tests, UI, build, Playwright passent sous Node supporté |
| Reproductibilité | lockfile, checksum, build id, `/api/version` |
| Performance | budgets adoptés atteints sur benchmarks de référence |
| Sécurité | threat model du profil, tests de non-fuite, auth si partagé |
| Observabilité | logs, métriques, health/readiness/version |
| Opérations | runbooks startup, rollback, backup/restore, incident, upgrade |
| Accessibilité | clavier + fallback pour chaque renderer |
| Documentation | guides utilisateur, intégrateur, développeur, opérateur publiés |


## CI / qualification automatique

- `.github/workflows/ci.yml` exécute les gates sur push/PR avec Node 24.15.0 ;
- `.github/workflows/release.yml` qualifie les tags `v1.*`, vérifie les métadonnées reproductibles, exécute la suite complète et produit un bundle + SHA-256 ;
- le workflow doit rester rouge tant que `package-lock.json` n'est pas commité et que `release:check` n'est pas entièrement vert.

## Checklist finale

- [ ] Kristal v6 reste l'autorité canonique.
- [ ] NavigationHints ne contiennent aucun code exécutable.
- [ ] QuerySpec ne contient aucune préférence de vue.
- [ ] Reader Policy s'applique avant toutes les surfaces secondaires.
- [ ] NavigationPlan est versionné, dérivé et explicable.
- [ ] Toutes les recettes ont un fallback accessible.
- [ ] Les projections sont bornées/paginées/LOD.
- [ ] Un Kristal inconnu reste navigable.
- [ ] Aucune branche planner basée sur un nom de domaine.
- [ ] Actionability ne devient jamais permission.
- [ ] Les pertes d'import v6 sont explicites.
- [ ] Les caches sont invalidés par fingerprint.
- [ ] Les erreurs sont structurées et corrélables.
- [ ] Health, readiness et version existent.
- [ ] Lockfile commité et `npm ci` obligatoire.
- [ ] Playwright couvre les parcours critiques.
- [ ] Golden corpus contient tests positifs et négatifs.
- [ ] Benchmarks et seuils de régression automatisés.
- [ ] Threat model et runbook existent pour le profil déployé.

## Définition stricte

« Architecture correcte » ou « tests unitaires verts » ne suffit pas. La release 1.0 est un **état opérationnel qualifié**, pas seulement un numéro de version.
