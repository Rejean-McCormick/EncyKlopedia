# EncyKlopedia — Overlay v27 (production de packs et Kristals cumulatifs)

**Installation :** extraire ce ZIP à la racine de `C:\mycode\EncyKlopedia\EncyKlopedia` en conservant l'arborescence. **Aucun installateur**. Les fichiers de l'overlay sont nouveaux : aucun fichier existant ne doit être remplacé.

**Commande à lancer dans PowerShell 7 depuis la racine du dépôt :**

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\PRODUIRE_KRISTALS_V27.ps1" -Action Packs -MaxPacks 5
```

Les ZIP à m'envoyer **un par un** seront créés dans :

```text
D:\EncyKlopedia\30_working\production_kristals_v27\packs\PACK_V27_000001.zip
```

Le moteur extrait chaque source Wikipédia **en entier**, puis assemble des packs adaptés à une analyse IA sélective. Les faits des retours IA seront cumulatifs après une deuxième commande `-Action Import`, décrite dans `docs/UNESCO_PRODUCTION_KRISTALS_V27.md`.

**Important :** la fusion ajoute des connaissances à une **base Kristal privée de travail**. Elle n'admet pas automatiquement de KQ, KP, KA ou KS dans le Framework canonique et ne modifie pas les réalisations v11–v26 déjà présentes. Les connaissances produites pourront être révisées plus tard.

**Sources locales nécessaires** (déjà construites lors des étapes précédentes) :

- Catalogue unifié v25/v26 sur D: (`catalogue_global_unesco_wikipedia_v25.sqlite`)
- Index d'offsets v21 sur D: (`wikipedia_en_direct_pages_v21.sqlite`)
- XML Wikipédia EN décompressé sur D: (environ 110 Gio)

Le programme vérifie les liens entre les sources et refuse les mélanges de versions, plutôt que de relancer l'importation massive.
