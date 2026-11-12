# EncyKlopedia v30 — Centre de production optimisé

**Installation initiale** : décompresser cet overlay **à la racine** de `C:\mycode\EncyKlopedia\EncyKlopedia` (fusionner les dossiers). Il contient uniquement les nouveaux fichiers du poste v30; il ne remplace ni les bases du disque D: ni les moteurs v27/v28 déjà installés.

**Une seule commande** dans PowerShell, depuis cette racine :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\LANCER_POSTE_CHATGPT_V30.ps1"
```

Le navigateur s'ouvre sur un serveur **local** `http://127.0.0.1:<port>/`, avec dix postes. Garder la fenêtre PowerShell ouverte.

## Routine

1. Cliquer **Préparer toute la prochaine vague** : génération incrémentale des packs Wikipédia v27 (objectifs réduits à 18 000 mots/16 articles, sans tronquer les articles), découverte v28 seulement si aucun retour v28 n'est en cours, indexation complète des propositions et alimentation de la file.
2. Cliquer **Copier + ZIP** dans chacun des dix postes. Le poste tente de copier dans le presse-papiers Windows le prompt et le fichier ; un ZIP est **toujours téléchargé** comme repli. Certains navigateurs collent seulement le texte : joindre alors le ZIP téléchargé à la conversation ChatGPT.
3. Traiter les dix tâches dans dix conversations indépendantes. L'interface n'exécute aucune conversation et n'appelle aucune API de ChatGPT.
4. Déposer dans la zone principale un ou plusieurs **ZIP de retour**, contenant soit les deltas JSON v27, soit des décisions CSV v28 **de trois colonnes, une ligne pour chaque candidat (HOLD explicite)**. Les identifiants et empreintes sont vérifiés; les vrais moteurs v27/v28 importent les données. Le poste terminé reçoit immédiatement la tâche suivante.
5. Si une revue est incomplète ou entièrement `HOLD`, confirmer explicitement sa clôture après contrôle. Les retours incorrects restent visibles dans la liste **Retours reçus et refusés**; un poste en erreur peut être réessayé.

## Corrections apportées à la v29

- **File durable SQLite** `D:\EncyKlopedia\30_working\poste_chatgpt_v30\station_v30.sqlite`; état, retours, tâches et dix affectations conservés après fermeture/redémarrage.
- **Pagination intégrale** : l'index v28 parcours tous les candidats non définitivement classés, sans plafonnement aux 3 000 premiers. Seulement vingt lots v28 préparés d'avance pour éviter une explosion d'archives; le reste demeure dans l'index et est chargé progressivement.
- **Provenance immuable** : la découverte v28 est reportée tant qu'une revue en cours risquerait d'être invalidée par une nouvelle preuve. Chaque tâche est attachée à sa source et à son SHA-256.
- **Réutilisation des revues précédentes** : les `HOLD` des fichiers `tools\unesco_pilot\v28_data\DECISIONS_ARTICLES_RELIES_V28*.csv` sont mémorisés sans être remis en file; option de réexamen volontaire de 500 HOLD.
- **Taille adaptative** des revues, selon la densité des preuves (55 à 110 candidats); packs Wikipédia plus petits par défaut, tout en préservant le texte intégral.
- **Réception multiple**, erreurs par fichier visibles, reprise après interruption et importation contrôlée; aucune exécution de code provenant des ZIP de retour.
- **Mise à jour logicielle séparée** : un overlay muni du manifeste `ENCYK_OVERLAY_MANIFEST_V30.json` peut être prévalidé, installé **après confirmation**, sauvegardé et annulé. La vérification SHA ne prouve pas que le code est digne de confiance; il faut vérifier sa provenance. Un redémarrage est requis après installation ou retour arrière.
- Si un `state.json` v29 existe et que la base v30 est vide, tentative de migration prudente des tâches v29 encore accessibles. Les anciennes données restent intactes.

## Respect des données

Les sources Wikipédia sont conservées dans leur intégralité, les bases source/index sont en lecture seule pour les phases de production, les classements UNESCO restent documentaires, et les connaissances Kristal demeurent des **candidats privés**. Aucune admission canonique ni publication n'est réalisée par v30.

**Limites** : la validation de compatibilité a été faite sur copies/simulations en environnement Linux, pas encore sur le Windows réel. Les traitements de plusieurs millions d'articles demanderont plus de mémoire/temps et une orchestration distribuée. Le presse-papiers peut être limité par les navigateurs; télécharger et joindre le ZIP reste fiable.
