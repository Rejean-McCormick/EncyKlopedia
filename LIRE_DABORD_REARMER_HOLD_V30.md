# EncyKlopedia — repartir sur les HOLD avec les packs enrichis

**Ce n'est PAS une reinitialisation generale d'EncyKlopedia.**

Ce correctif ne change pas le code du poste ni les bases de connaissances.
Il remet en circulation seulement :

1. Les tâches UNESCO v28 `NEEDS_CONFIRMATION` avec **zéro APPROVE et zéro REJECT** (tous HOLD), tant que les fichiers locaux de la tâche et leurs empreintes SHA-256 sont encore valides. Leur même identifiant et leurs preuves sont conservés. Le retour tout-HOLD est conservé en historique.
2. Les anciens candidats du `review_index` en état `HOLD`, qui repassent à `PENDING` pour être reprogrammés plus tard avec de nouveaux lots. Les tâches déjà `DONE` restent archivées telles quelles.

Sont explicitement protégés : tout APPROVE ou REJECT validé (`DECIDED`), toutes les revues partielles `NEEDS_CONFIRMATION` ayant des APPROVE/REJECT, les jobs v27 et toutes les bases v25/v27/v28. Aucune nouvelle découverte v28 n'est lancée par ce script.

## Une commande

1. **Fermer le poste v30** (navigateur et fenêtre PowerShell). Le script bloque si le processus Python v30 tourne encore.
2. Extraire le ZIP dans `C:\mycode\EncyKlopedia\EncyKlopedia`.
3. Ouvrir PowerShell 7 et exécuter :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\mycode\EncyKlopedia\EncyKlopedia\REARMER_HOLD_V30.ps1"
```

Le script effectue une sauvegarde SQLite complète dans :
`D:\EncyKlopedia\30_working\poste_chatgpt_v30\SAUVEGARDES_RESET_HOLD_V30\<horodatage>\`

Il vérifie l'intégrité de la sauvegarde, applique toutes les modifications dans une transaction et relance v30. Le journal indique les tâches réarmées et les candidats HOLD réouverts.

## Après redémarrage

- Au poste 10, retrouver la tâche précédemment « HOLD à confirmer », désormais « Prêt à transmettre » et cliquer **ZIP** / **Copier + ZIP**.
- Si l'extension **Packs UNESCO enrichis** est installée, le ZIP téléchargé fournit davantage de contexte, sans modifier le CSV ni les identifiants.
- Pour que les anciens HOLD réouverts deviennent de nouveaux lots, cliquer **« Reprendre depuis les fichiers existants »**, et non pas « Préparer toute la prochaine vague » (qui essaierait de relancer v27 et exigerait le XML manquant).
- Un historique ancien peut toujours montrer des HOLD comptabilisés dans des tâches `DONE`; c'est intentionnel pour conserver l'audit des revues précédentes. Leur réexamen ne retire pas rétrospectivement l'historique.
- Si une tâche tout-HOLD n'est pas réarmée faute de source locale, le script l'indique et la laisse intacte.

## Aperçu seulement

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\mycode\EncyKlopedia\EncyKlopedia\REARMER_HOLD_V30.ps1" -Apercu
```

## Ne pas relancer le poste après reset

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\mycode\EncyKlopedia\EncyKlopedia\REARMER_HOLD_V30.ps1" -SansRelancer
```

Aucun ancien ZIP téléchargé n'est requis : le correctif utilise les chemins locaux et empreintes déjà enregistrés par v30. Cependant les **fichiers locaux sources** doivent être présents pour réarmer une tâche tout-HOLD particulière.
