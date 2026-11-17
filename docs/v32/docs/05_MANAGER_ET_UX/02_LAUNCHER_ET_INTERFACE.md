# Launcher `.pyw` racine et structure proposée du méga-repo

**[CIBLE — non installé]** Un seul dépôt **EncyKlopedia** et un double-clic racine sur `EncyKlopedia.pyw`. L'extension `.pyw` évite la console sous Windows quand Python/Tk sont disponibles. Une interface graphique seule ne suffit pas : exposer aussi la même application via CLI pour tests, automation et dépannage. Ne pas créer de second centre de production indépendant.

## Arborescence indicative (conception, non livraison de code)

```text
EncyKlopedia/
  EncyKlopedia.pyw             # lanceur graphique léger, au root
  encyk.py                     # même composition root, CLI: doctor/prepare/jobs/import/report
  README.md
  AGENTS.md
  docs/                       # cette documentation, à transférer lors du refactor
  src/encyk/
    app/                      # use cases + orchestration
    domain/                   # IDs, branch, subject, claim, selected candidate
    adapters/
      unesco/                 # snapshots UNESCO / P3916 / RDF
      wikidata_skope/         # appels Skope installé, aucun fork
      wikipedia/              # index SQL + XML source
      kristalizer/            # optionnel et EXTERNE, aucun fork
      legacy/                 # enveloppe temporaire moteurs v25/v27/v28/v30
    infrastructure/
      jobs/                   # SQLite locale, outbox logique minimale, curseurs
      zip_packs/              # construire/ouvrir les lots
      storage/                # Kristal privé et références
    ui/                       # une vue de travail principale, état dérivé de l'application
  tests/                      # tests de flux, fixtures synthétiques, non 125 Go
  tools/                      # utilitaires absorbés et vraiment utiles
  legacy/                     # archives de code v31 et adapters transitoires
  examples/                   # petites fixtures sans données sensibles
```

L'arborescence **n'autorise pas** à déplacer Skope, Kristalizer, la médiathèque partagée, les bases D: ou la première branche. Elle aide le futur développeur à donner un emplacement au code récupéré; les anciens dossiers pourront être archivés une fois le remplacement démontré.

## Composition root : une seule initialisation

`EncyKlopedia.pyw` ne doit contenir ni SQL, ni logique de sélection, ni extraction XML. Il fait uniquement : résoudre les chemins, charger un profil, démarrer les services métier, ouvrir la fenêtre et afficher un diagnostic compréhensible si une source est absente. `encyk.py` importe la même composition, sans initialiser Tk.

Exemples de commandes **[CIBLE, non implémentées]** :

```powershell
python encyk.py doctor
python encyk.py branches list
python encyk.py discover --branch unesco.mt1.10 --dry-run
python encyk.py prepare --branch unesco.mt2.1 --max-jobs 10
python encyk.py jobs list
python encyk.py import --path D:\EncyKlopedia\retours\retour.zip
python encyk.py report --branch unesco.mt2.1
```

Les commandes exactes et les noms de branches doivent être décidés pendant l'implémentation, pas considérés ici comme interfaces existantes.

## Écran initial — informations et opérations

```text
[EncyKlopedia V32]   [Périmètre : 3 branches]    [Sources : prêtes 4/5]

Production  : 5 postes occupés / 10      En sélection : 3   Enrichissement : 2
Disponibles : 8 200 candidats           En attente de retour : 5

[Préparer la prochaine vague]  [Importer les retours ZIP]  [Reprendre]

POSTE 1   SÉLECTION       4 000 couples     [Copier prompt + ZIP] [ZIP] [Détails]
POSTE 2   ENRICHISSEMENT    58 articles     [Copier prompt + ZIP] [ZIP] [Détails]
...

Résultat récent : 1 420 couples décidés ; 193 sujets retenus ; 1 162 faits ajoutés
Alertes : 1 source Wikipédia indisponible pour 28 pages [Voir la liste]

[Branches et couverture]  [Kristals privés]  [Diagnostics avancés]
```

Les nombres ci-dessus sont **illustratifs**, jamais des valeurs de production. Les labels et actions doivent découler d'un état métier interrogé, non de la présence de fichiers ZIP. « Préchargement » signifie que le ZIP est en cours de construction, pas qu'il est prêt à être téléchargé.

## États UI canoniques et verbes

| État métier | Affichage | Action |
|---|---|---|
| `queued` | En attente de préparation | Voir priorité |
| `preparing` | Préparation en cours | Voir progression / annuler si sûr |
| `ready` | Prêt à transmettre | Copier prompt + télécharger ZIP |
| `sent` | Envoyé, retour attendu | Déposer un ZIP / marquer transfert |
| `importing` | Import en cours | Voir traitement |
| `done` | Importé, détails disponibles | Voir résultats |
| `partial` | Import partiel | Corriger items rejetés |
| `failed` | Échec explicite | Réessayer opération ciblée |
| `unknown` | État non vérifié | Diagnostiquer, sans inventer succès |

La consommation humaine des chats n'est pas mesurable par la seule horloge locale. Éviter « IA travaille » si l'application ne peut pas le constater; préférer « ZIP remis, retour attendu ».

## UI recommandée d'après le codex UX

Garder 3–6 actions normales dans la vue de travail, déplacer configuration, rapport et migration dans « avancé ». Ne pas simplement ajouter un onglet « nouvelle production » à l'ancienne station si les deux revendiquent la même file. Ne pas relancer une découverte de plusieurs heures au double-clic. Préserver la sélection de branche et la position de lecture quand un pack est importé. Prévoir clavier et retours lisibles, sans consacrer le chantier initial aux couleurs ou marges.
