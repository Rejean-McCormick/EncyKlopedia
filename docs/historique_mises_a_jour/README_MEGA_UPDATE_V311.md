# EncyKlopedia — MÉGA MISE À JOUR CUMULATIVE V31.1

**Livraison de code** intégrant les outils V30/V31 et les améliorations V31.1. Python 3.12 / PowerShell 7.6. Conçu pour le dépôt `C:\mycode\EncyKlopedia\EncyKlopedia` et les bases `D:\EncyKlopedia`.

## Installation — une seule commande

Après téléchargement du ZIP dans `Téléchargements` :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -Command '$z=Join-Path $HOME "Downloads\EncyKlopedia_MEGA_MAJ_CUMULATIVE_V31_1.zip"; $d=Join-Path $env:TEMP "ENCI_MEGA_MAJ_V311"; Expand-Archive -LiteralPath $z -DestinationPath $d -Force; & (Join-Path $d "INSTALLER_MEGA_MAJ_V311.ps1")'
```

Redémarrer ensuite le poste :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\mycode\EncyKlopedia\EncyKlopedia\LANCER_POSTE_CHATGPT_V30.ps1"
```

## Fonctionnalités incluses

- Qualification globale multibranche sur les index Wikipédia existants, profils conservés, QID candidats, lexical corrigé, cache reprenable.
- Découverte v28 par index SQL en alternative lorsque les offsets XML v21 sont incompatibles. Provenance SQL explicite, aucune citation inventée.
- Routage multibranche des tâches de la station ; revues par branche distincte et retour vers le moteur v28 natif.
- Réserve des candidats faibles (`DEFERRED`) avec exploration dans les packs ; aucun rejet automatique.
- Packs v28 d'environ **300 candidats** selon le budget, sans toucher aux tâches déjà gelées.
- Statistiques HTML/JSON sur station, catalogue, Kristal, réserves et branches.
- Outils V30 précédemment livrés et documentation de référence V31 avec addendum V31.1.

## Après installation

```powershell
# Étendre le catalogue aux branches réellement disponibles et découvrir leurs candidats
pwsh -NoProfile -ExecutionPolicy Bypass -File .\ACTIVER_TOUTES_BRANCHES_V311.ps1

# Inventorier en continu les pages ns=0 et leurs hypothèses de branches
pwsh -NoProfile -ExecutionPolicy Bypass -File .\LANCER_QUALIFICATION_GLOBALE_V31.ps1 -Tout

# Tableau de bord global HTML et JSON
pwsh -NoProfile -ExecutionPolicy Bypass -File .\GENERER_STATS_GLOBALES_V31.ps1

# Retirer 300 candidats de la réserve différée pour une nouvelle exploration
pwsh -NoProfile -ExecutionPolicy Bypass -File .\OUVRIR_EXPLORATION_V311.ps1 -Propositions 300
```

**À savoir** : si les manifestes v25 locaux ne décrivent qu'une branche, aucun programme ne peut inventer les autres branches UNESCO. Le codage multibranche est prêt, leur contenu doit provenir des données UNESCO disponibles. Les performances sur la vraie base Wikipédia et le fonctionnement de bout en bout sur Windows restent à vérifier après installation.

Les bases sources et les anciennes tâches ne sont pas remaniées. Les scripts du poste v30 et de contexte v28 sont remplacés uniquement lorsqu'ils correspondent aux versions déjà auditées (v30 ou v31).
