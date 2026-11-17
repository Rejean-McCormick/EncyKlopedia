# EncyKlopedia v31.8 — Mode Synthèse approfondie (Kristal v27)

## Objet

Améliorer **la profondeur intellectuelle et le rappel des connaissances structurantes** sans transformer EncyKlopedia en copie de Wikipédia. Le traitement d'un pack en moins de dix minutes ne démontre ni qu'il soit complet ni qu'il soit superficiel. La qualité se mesure par la valeur, les sources et les omissions corrigées, pas par la durée ni le volume brut de faits.

Ce correctif est construit à partir de `znapshot_EncyKlopedia_11151005.zip` et préserve les correctifs v31.7/v31.7.1 présents dans ce snapshot. **Aucune base de production, aucune tâche, aucun pack antérieur et aucune preuve UNESCO ne sont modifiés par l'overlay.**

## Changements apportés

1. **Six passes documentaires** dans `INSTRUCTIONS_CHATGPT.md` des nouveaux packs et dans la consigne de la station : inventaire, extraction des faits structurants, seconde lecture ciblée, synthèse, vérification des preuves, audit final des omissions.
2. **Affichage de la station** : le bandeau distingue désormais le mode Kristal v31.8 de la taille UNESCO v31.7, sans toucher aux limites de production.
3. **Inventaire des sections** dans le dossier de lecture existant `DOSSIER_PRIORITAIRE_KRISTAL_V316.jsonl` : nouvelle clé facultative `section_inventory` conservant l'ordre des sections (titre, volume approximatif, indicateur bibliographique et indice de priorité). Les `samples` restent des extraits exacts mais non exhaustifs. L'inventaire guide vers des sections non représentées dans les six extraits prioritaires, et n'est PAS une preuve indépendante. Le nom et le schéma v316 existants restent reconnus.
4. **Contrat prospectif explicite** `synthesis_audit=encyklopedia.kristal-synthese-approfondie.v318/1` dans les manifestes produits APRÈS installation. Les anciens manifestes, deltas et packs v27 ne sont pas réécrits ni soumis rétroactivement aux nouvelles contraintes.
5. **Validation renforcée des nouveaux deltas seulement** : un `coverage_note` doit comporter une ligne par article, commençant par `enwiki:PAGE_ID |`, indiquant dimensions examinées, faits retenus et limites/omissions ; chaque connaissance exige une citation verbatim de 20 à 500 caractères présente dans le wikitext de la révision citée. L'inventaire des sections doit être cohérent avec le texte intégral. Les entrées à zéro fait restent possibles ; aucun quota numérique n'est imposé.
6. **Contrats inchangés** : `encyklopedia.wikipedia-fulltext-pack.v27/1` et `encyklopedia.kristal-ai-delta.v27/1`, noms de fichiers, `page_id`, `revision_id`, `pack_sha256`, structure des revendications, recherche Kristal privée et non canonique. La taille des nouveaux packs reste **120 articles, 400 000 mots et 60 Mio**. UNESCO reste à **4 000 propositions**, sans modification du routage ni du gel des preuves.

## Limites de ce contrôle

- Une citation exacte peut néanmoins être **sémantiquement insuffisante** pour une affirmation. La vérification automatisée ne démontre ni l'exactitude de Wikipédia ni l'exhaustivité encyclopédique.
- La présence de 120 lignes de couverture ne prouve pas à elle seule que les 120 articles ont été lus en profondeur ; cette obligation est intellectuelle et doit faire l'objet d'une évaluation indépendante sur échantillon.
- L'inventaire des sections mesure leur présence, non leur pertinence. Le dossier prioritaire ne remplace jamais les articles complets.
- Les retours d'anciens packs sans marqueur v31.8 conservent leur validation v27 historique pour éviter les régressions et les tâches bloquées.
- Cette mise à jour ne promet pas une augmentation chiffrée des connaissances. Une augmentation artificielle serait contraire à l'objectif.

## Installation et retour arrière

1. Fermer les opérations actives et conserver la sauvegarde de la station.
2. Importer cet **overlay logiciel** dans **Mises à jour logicielles**, jamais dans **Retours encyclopédiques**.
3. Exiger la prévalidation SHA-256 des fichiers existants et refuser toute divergence (version plus récente ou différente). Ne pas écraser manuellement.
4. Confirmer, puis redémarrer la station. Les packs déjà produits restent inchangés ; seules les nouvelles générations portent le contrat v31.8.
5. Le retour arrière logiciel est pris en charge par la station si aucun fichier installé n'a été modifié ultérieurement. Les packs déjà générés en v31.8 conservent leur marqueur et peuvent rester plus stricts qu'une ancienne version du moteur : ne pas les convertir/réécrire.

## Vérifications

```
python -m unittest discover -s tests -p 'test_synthese_approfondie_v318.py' -v
python -m unittest discover -s tests -p 'test_production_kristals_v27.py' -v
python -m unittest discover -s tests -p 'test_kristal_synthese_v316.py' -v
python -m unittest discover -s tests -p 'test_unesco_4000_v317.py' -v
```

Ces tests utilisent uniquement des archives et bases temporaires synthétiques. Les tests historiques ont été adaptés pour fournir des citations exactes et des bilans d'articles conformes aux packs nouveaux, sans supprimer les tests de compatibilité des anciens packs.

**Évaluation recommandée avant d'augmenter les packs :** reprendre sur copie du pack 000266, comparer sa synthèse actuelle aux connaissances supplémentaires produites sous v31.8, classer manuellement un échantillon en « essentiel / redondant / insuffisamment étayé » et noter les omissions. Ce correctif ne modifie ni ne réimporte le pack 000266.
