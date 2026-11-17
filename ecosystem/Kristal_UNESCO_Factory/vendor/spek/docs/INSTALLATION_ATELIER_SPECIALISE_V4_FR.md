# Installer l'atelier Spek spécialisé (mise à jour)

Ce paquet s'applique au Spek version « slugs canoniques » du 2 novembre 2026.

## Correctif (recommandé si le dépôt fonctionne déjà)

1. **Fermer Spek** et préserver les modifications locales non committées (`git status`).
2. Si le Spek existant est ici : `C:\mycode\Spek_Semantic-publishing\Spek`, extraire le ZIP de correctif dans **`C:\mycode\Spek_Semantic-publishing`** (son parent). Ne pas créer `Spek\Spek`.
3. Accepter le remplacement des fichiers **du correctif** ; les sources des Kristals et le `.git` ne sont pas inclus.
4. Lancer `Spek\START_SPEK.bat` ou `Spek\Spek_Template_Manager.pyw`.
5. Ouvrir un Kristal parmi AI, Accounting, Aerospace, Aging, Agriculture ; « Explorer les assertions dans la composition » doit être disponible si l'empreinte du fichier étudié correspond.

Si d'autres modifications locales ont été faites aux mêmes fichiers du correctif, les comparer avant remplacement. Le correctif contient un sous-ensemble du dépôt : il ne supprime pas les autres fichiers du dépôt.

## Dépôt complet

Le ZIP complet contient `Spek/` et peut être extrait dans le dossier parent de ce répertoire. Pour préserver l'historique, ne pas effacer `.git` : restaurer les fichiers du ZIP dans un clone existant puis vérifier `git diff`. Le ZIP ne contient pas de dépôt `.git`.

## Ce qui est activé

- 27 layouts Spek exécutables sur **données explicitement sélectionnées et réalisées** (8 existants + 19 nouveaux).
- 19 contrats d'aperçu structurel privé pour les revues des cinq premiers Kristals.
- Consultation du registre des 127 propositions, sans assignations approuvées.
- Exemple fictif sous `examples/specialized/`, sans faits canoniques ni résultat SemantiK.
- Aucun push ni publication.

## Diagnostic

```powershell
cd C:\mycode\Spek_Semantic-publishing\Spek
py -3 Spek_Template_Manager.pyw --diagnostic
py -3 -m unittest discover -s tests -q
```

Sur un poste Python avec Tkinter et ReportLab, le lanceur et la compilation PDF fonctionnent ; la vérification effectuée ici était sous Linux avec interface graphique virtuelle, **pas sur ton installation Windows**.
