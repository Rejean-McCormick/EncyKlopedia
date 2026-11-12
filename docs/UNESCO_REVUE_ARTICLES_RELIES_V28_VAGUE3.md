# EncyKlopedia — Revue UNESCO v28 / vague 3

Overlay a decompresser directement a la racine : `C:\mycode\EncyKlopedia\EncyKlopedia`.

Commande unique :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\APPLIQUER_REVUE_UNESCO_V28_VAGUE3.ps1"
```

Resultat attendu : `V28_VAGUE3_OK`.

## Decisions

- 1 500 paires de propositions issues de la sequence 35 du catalogue.
- 100 `APPROVE` : 99 articles distincts, sans supposer combien sont deja presents au catalogue.
- 557 `REJECT` : absence de lien direct avec le concept cible, malgre un voisinage Wikipedia.
- 843 `HOLD` : informations insuffisantes ou liens uniquement contextuels non tranches.
- 1 117 paires deja en attente lors de la vague 2; 410 ont ete rejetees apres nouvel examen, 707 demeurent en attente.

## Garanties

- Seuls les champs `decision` et `justification` du CSV ont ete modifies.
- SHA-256 du CSV : `e830ffcc1b559f2cbcb1787232f69c4fc2ee515d9f6e750776203158a08553f9`.
- Les identifiants de propositions, pages et concepts ainsi que les empreintes de preuve sont inchanges.
- Controle via le lecteur reel `read_decisions` du moteur v28.1.
- Le lanceur execute d'abord `Apply -DryRun`, ensuite `Apply` et enfin `Status`; chaque etape est bloquante en cas d'erreur.
- Ce classement est **documentaire et provisoire** : l'export ne fournit pas le texte integral des articles cibles et ne prouve pas les connaissances contenues.
- Les Kristals v27 et la base Wikipedia ne sont pas modifies par le classement.
- Le nombre de nouvelles pages n'est pas determine avant `V28_APPLY_OK` sur la machine locale.
