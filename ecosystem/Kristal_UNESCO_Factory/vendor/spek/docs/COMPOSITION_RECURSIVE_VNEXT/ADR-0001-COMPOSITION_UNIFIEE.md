# ADR-SPEK-001 — Une grammaire de composition, incluant la rhétorique

- **Statut : ADOPTÉ POUR IMPLÉMENTATION INCRÉMENTALE** ; moteur vNext distinct exécuté localement, publication non qualifiée.
- **Date : 2026-11-02.**
- **Décision visée :** architecture de la prochaine version de Spek.

## Contexte

Spek contient des layouts typés, une bibliothèque et un dialogue de formulation par slot. Les compositions Wiki sont aujourd'hui principalement plates et les templates peuvent se rendre comme des cartes avec de nombreux titres. L'objectif utilisateur exige une progression documentaire répétable et lisible, faite de petites réalisations SemantiK standardisées : des templates peuvent en contenir d'autres, répéter des motifs trois fois ou plus, puis changer de mise en page sans changer les faits.

## Décision adoptée pour le moteur récursif

Adopter un **graphe de templates typés, versionnés, composables et résolus déterministement**. `rhetorical` devient une catégorie du même registre et du même moteur, non un système parallèle. Le renderer projette le graphe logique vers un document accessible ; les titres/logiques de slots ne deviennent pas forcément des en-têtes visibles. Le dialogue avec SemantiK se fait **à la feuille linguistique**, sans modification d'obligations ni reformulation libre.

## Raisons

- Une seule règle de cardinalité, validation, traçabilité et répétition pour tous les templates.
- Réutilisation transversale (Wiki, livres, rapports, pédagogie).
- Standardisation voulue ; lecture moins artificielle par l'agencement visuel, pas par une variation stylistique aléatoire.
- Frontières de responsabilité préservées : IA/Manager pour décisions éditoriales, SemantiK pour phrases, Spek pour structure et surface.
- Compatibilité progressive avec les 27 layouts existants.

## Alternatives écartées

1. **Moteur rhétorique séparé** : doubles règles de validation et imbrication incohérente.
2. **LLM de reformulation au runtime** : non déterministe, risque d'inférences et perte de provenance.
3. **Rendu de toute imbrication en cartes/titres** : bruit visuel, empilement de niveaux sans pertinence lecteur.
4. **Template choisissant lui-même les faits** : usurpe la sélection éditoriale et les autorisations.
5. **Réécriture totale du moteur actuel** : forte régression ; migration incrémentale préférée.

## Conséquences

- Nouveau contrat de composition et de rendu versionné nécessaire.
- AST résolu, validateurs de graphes et règles de jointure strictes nécessaires.
- Les 27 layouts actuels restent supportés ; les nouvelles capacités ne sont pas rétro-projetées silencieusement.
- Les templates rhétoriques ne nécessitent pas, dans leur première version, de nouveaux actes communicatifs SemantiK ; ils composent des unités produites par les actes disponibles.
- Des tests de confidentialité et d'accessibilité plus exigeants sont nécessaires.

## Questions restantes avant qualification du moteur complet

- Niveaux de profondeur/fan-out acceptés et politique de `repeat` dépendante des collections explicites.
- Contrat exact de `inline-safe`, s'il est réellement nécessaire ; premier jalon en `block` uniquement.
- Stratégie d'étiquettes non factuelles localisées vs réalisation linguistique.
- Format et version du `ResolvedComposition` privé, avec conservation des liens de traçabilité hors sorties lecteur.
- Mode de migration des sections plates existantes ; maintien du chemin historique obligatoire.

## Références

- [Vision](01_VISION_ET_FRONTIERES.md)
- [Modèle](02_MODELE_COMPOSABLE.md)
- [SemantiK](04_DIALOGUE_SEMANTIK.md)
- [Patterns](07_PATTERNS_RETENUS.md)
- Fichiers existants : `spek/slot_dialogue.py`, `spek/core.py`, `spek/render.py`
