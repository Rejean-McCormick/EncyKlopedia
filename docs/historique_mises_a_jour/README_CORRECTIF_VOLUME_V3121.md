# EncyKlopedia v31.2.1 — Correctif conservateur du tampon multibranche

**Type** : overlay logiciel v30, à prévalider puis à appliquer explicitement dans la station.
**Base de départ requise** : moteur `poste_chatgpt_v30.py` v31.2, SHA-256
`2857faf01dc927f7e0222fe3c0d033a5d3750895baf6b179ebda5de704e97629`.

## Défaut corrigé

Dans v31.2, `_prepare_v28()` comptait les tâches ouvertes de toutes les branches,
mais calculait sa cible et utilisait sa condition de boucle comme si seules les
tâches de la branche historique entraient dans la file. Quand une découverte
multibranche existait, l'ordonnanceur pouvait préparer des packs historiques
au-delà de `QUEUE_BUFFER=20` si des branches secondaires occupaient déjà les
20 places. Cela augmentait inutilement le nombre de preuves et de lots à
suivre, surtout pendant la transition des lots de 110 vers 880.

## Correction

- Le nombre global de tâches UNESCO ouvertes est désormais comparé à la limite
  de 20 **avant toute création**.
- La part de la branche historique est calculée distinctement par absence de
  route `v311_job_routes`, sans modifier les tâches historiques.
- Les nouvelles tâches sont créées seulement si **les deux** limites (globale
  et part historique) permettent une création.
- Les tailles 880 / 24 articles / 80 000 mots et le budget 3 200 ne changent pas.

## Invariants préservés

Ce correctif ne réinitialise rien. Il ne modifie aucun ZIP, source, historique,
ligne SQLite, `candidate_id`, `evidence_sha256`, signature de branche, citation,
statut HOLD, décision, contrat d'import v28, article Kristal ou autorisation de
publication. Les tâches déjà préparées, notamment les lots UNESCO de 110,
restent terminables normalement. La découverte demeure gelée pendant les
retours UNESCO non clos. Les connaissances Kristal restent privées et
non canoniques.

## Installation contrôlée

Dans la station ouverte par `LANCER_POSTE_CHATGPT_V30.ps1`, utiliser **la
fonction de mise à jour logicielle** (et non le dépôt des retours de
connaissances) pour prévalider `ENCYK_OVERLAY_VOLUME_V3121.zip`, inspecter les
empreintes, appliquer puis redémarrer la station. La station sauvegarde le code
précédent et permet un retour arrière. Si le code local est différent de
l'empreinte ci-dessus, l'overlay doit être refusé : ne pas forcer.

Vérification après redémarrage, dans le dépôt Windows :

```powershell
python -m unittest discover -s tests -p 'test_*v31*.py' -q
python -m unittest discover -s tests -p 'test_volume_backpressure_v3121.py' -q
```

**Validation effectuée** : tests synthétiques du tampon, validation des imports
et empreintes sur copie du code dans un environnement Linux. Aucune exécution
sur les bases ou sur la station Windows de production n'est affirmée.
