# EncyKlopedia v31.6.1 — Préchargement automatique des transferts

## Objectif

Déplacer le travail coûteux de `Copier + ZIP` vers le démarrage de la station et le renouvellement de chaque poste. Les **10 postes actifs seulement** sont préchargés; les milliers de tâches futures ne sont pas réécrites ni préchargées. Le délai initial se produit en arrière-plan, avec un compteur de progression visible dans la section « Mode Synthèse ».

## Changements

- La station construit et vérifie à l'avance les ZIP UNESCO enrichis, à partir du cache documentaire existant, et vérifie les ZIP Kristal originaux. Aucun identifiant, fichier source, preuve figée, statut de tâche, ZIP original, importateur ni base documentaire n'est modifié par le préchargement.
- Quand un nouveau poste est attribué après import ou préparation, le préchargement se relance pour cette tâche. Les autres postes déjà prêts restent disponibles pendant la préparation.
- L'URL de téléchargement et le bouton `Copier + ZIP` réutilisent le même chemin préparé. Les hashes SHA-256 des sources et du résultat enrichi sont **toujours vérifiés au clic**, ainsi que la provenance des entrées UNESCO; un changement déclenche une nouvelle préparation ou un refus, jamais une utilisation silencieuse d'une preuve modifiée.
- Le presse-papiers Windows est préparé directement avec `CF_UNICODETEXT` et `CF_HDROP`, sans lancer `powershell.exe` à chaque clic. L'ancienne procédure PowerShell est conservée en secours si l'API Windows refuse l'accès.
- L'interface distingue `Préchargement…`, ZIP prêt et échec. En cas d'échec, le bouton reste disponible comme mode secours (et peut alors être plus lent).
- Pas de nouvelle préparation de vague nécessaire pour bénéficier du préchargement. Le redémarrage de la station est nécessaire après installation.

## Protections conservées

- Preuves UNESCO v28 et fichiers CSV originaux figés. Aucun réexamen ou nouvelle découverte automatique.
- ZIP Kristal v27 et lots existants intacts, aucun reclassement ni canonisation.
- Bases SQLite des tâches et imports conservées, mêmes règles d'import.
- Overlay installé **explicitement** et uniquement après contrôle des empreintes de version. Il inclut sauvegarde logicielle et retour arrière.
- Les limites v31.6 de 120 articles, 400 000 mots et 880 propositions UNESCO restent inchangées.

## Validation et limites

Le format binaire du presse-papiers Windows (texte Unicode + fichier glissé) est vérifié par test unitaire. L'appel réel aux API `user32/kernel32` n'a pas pu être testé sur Windows ici; le PowerShell existant reste le secours. La rapidité des clics dépend encore du débit disque, du navigateur et du presse-papiers. Le préchargement ne copie pas le fichier dans ChatGPT lui-même; selon le navigateur, le ZIP téléchargé doit encore être joint manuellement.

## Tests

Depuis le dépôt :

```powershell
& "C:\Users\rejea\AppData\Local\Programs\Python\Python312\python.exe" -m unittest discover -s tests -p 'test_prechargement_postes_v3161.py' -v
```

Six tests : dix postes, cache réutilisé, invalidation hash, fonctionnement concurrent pendant préchargement, renouvellement de poste, format presse-papiers, provenance UNESCO. Les tests historiques de v30 avaient déjà deux échecs dans le snapshot d'origine et ne constituent pas un signal de régression v31.6.1.
