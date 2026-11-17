# Version 1.6 : lecture BZIP2 Wikidata réparée

Après la réussite technique de Spek v1.5, l’import des faits complets restait bloqué dans Python 3.14. Cette mise à jour ajoute un lecteur CPython 3.13 isolé avec accès aléatoire via les index Skope existants. Voir `NOTES_VERSION_1_6.md` pour le détail, les traces et les limites.

**Installation :** décompresser dans `C:\mycode\Kristal` en remplaçant seulement `Kristal_UNESCO_Factory`; ouvrir `LANCER_FABRIQUE.cmd` et choisir « TOUT CONSTRUIRE + VALIDER ». Aucun ancien RUN n'est modifié. Le premier appel peut nécessiter Internet pour le lecteur privé.

**Diagnostic :** « Diagnostic WD », « Ouvrir faits WD », « Copier log » ou l’arbre d’artefacts.

---

# Fabrique encyclopédique UNESCO × Wikidata × Kristal × Spek

Application Windows Tkinter, lancement unique, journal en direct, sélection d'artifacts et copie directe. Version 1.5 expérimentale **locale et non publiable**. Corrige la distinction entre export P3916 réussi et rapprochements réellement résolus.

## Démarrer

1. Décompresser le ZIP entier (ne pas lancer directement depuis le ZIP).
2. Double-cliquer `LANCER_FABRIQUE.cmd` ou ouvrir directement `Fabrique_UNESCO.pyw` : l’environnement Python et `rdflib` sont vérifiés automatiquement.
3. Vérifier le chemin du Turtle UNESCO déjà téléchargé. Les chemins de l'index EncyKlopedia et du CSV P3916 sont optionnels.
4. Cliquer **TOUT CONSTRUIRE + VALIDER**. L'app exécute toutes les opérations d'un seul lancement et écrit le journal en direct. Un nouveau dossier `RUN-*` est créé, sans toucher aux RUN antérieurs.

Le journal `BOOTSTRAP_RUNTIME.log` est accessible directement depuis la liste des artefacts de l’application. Si nécessaire, la fabrique crée une venv privée et y installe `rdflib` sans modifier le Python système.

Le programme inclut les snapshots reçus : Authoring Kit v4.0.0-draft.4 et Spek vNext (source utilisateur du 3 novembre 2026), ainsi que les scripts `unesco_inventory_corrige.py` et `unesco_wikidata_bridge.py`. La version du kit est celle du snapshot fourni, pas un logiciel certifié ou mis à jour depuis le réseau.

## Nouvelle grammaire discursive Spek vNext

Voir `NOTES_VERSION_1_5.md`. La Fabrique intègre le nouveau Spek avec 62 templates rhétoriques versionnés, des instances et plans de dialogue FR/EN pour chaque concept, et 176 aperçus de microthésaurus. Bouton **Ouvrir discours Spek**. Ces aperçus sont faits de textes sources non révisés, et **pas** de réalisations GF qualifiées ni de preuves rhétoriques.

## Nouvelle entrée : faits complets Wikidata

La v1.4 peut retrouver le dump local EncyK (si son localisateur d’accès rapide Skope existe), ou lire les fiches déjà extraites (JSONL / dossier de parts Skope). Elle conserve les déclarations, références et qualificatifs hors canon, ajoute un **navigateur de faits** et enrichit les aperçus Spek par des données strictement étiquetées « non révisées ». Voir `NOTES_VERSION_1_4.md` pour la documentation et les limites.

## Ce qui est produit

- `01_INVENTAIRE/` : inventaire SKOS, relations et manifest.
- `02_WIKIDATA/JOINTURE/` : candidats P3916 et ambiguïtés, si un CSV P3916 est obtenu. `local_descriptions.jsonl` contient les descriptions FR/EN récupérées en lecture seule de ton SQLite, lorsqu’elles sont disponibles (candidats non approuvés).
- `03_KRISTALS/` : 88 espaces Kristal v9 construits par le **vrai Kit**. Le Logical Artifact est le **snapshot d'import UNESCO**, pas des identités KQ/KP approuvées. Les QID candidats restent dans `derived/`, hors canon.
- `04_SPEK/` : 88 volumes encyclopédiques FR/EN, 4 500 fiches de thésaurus, **compilés et vérifiés avec le vrai Spek**. Ouvrir `04_SPEK/index.html`.
- `05_IA_PROPOSITIONS/` : si IA activée, propositions locales Ollama en attente de revue, jamais dans le canon.
- `06_AUDIT/audit_p3916.html` : explorateur hors-ligne de **tous** les concepts avec recherche, filtres (uniques, ambigus, absents), accès aux URI UNESCO et QID Wikidata.
- `07_DISCOURS/` : 2 plans de composition par concept, dialogue FR/EN, audit des mouvements, pages de paragraphes privés fondés sur les sources.
- `RAPPORT_FINAL.json` et `fabrique.log` : bilan et détails. Le champ `wikidata_mapping_complete` est maintenant **faux** si des correspondances manquent ou restent ambiguës, même si l’export P3916 a abouti. `RAPPORT_INCIDENT.json` en cas d'échec.

## Frontières à respecter

Les 4 500 notices sont **des concepts de vocabulaire UNESCO**, pas 4 500 articles scientifiques. Une entrée avec un libellé mais sans définition n'est pas traitée comme une définition scientifique. Les textes FR/EN viennent du thésaurus ou de formulations d'interface locales ; ils ne sont **pas** générés ni certifiés par SemantiK Architect / GF. Spek produit un aperçu **démo non publiable**. L'application ne modifie ni les kristals existants ni l'index SQLite et n'exécute aucune synchronisation, publication ou activation.

L'export P3916 de Wikidata utilise WDQS si aucun CSV local n'existe. En cas d'échec réseau ou d'absence de P3916, l'application produit quand même les 88 cristaux *à partir de l'UNESCO*, signale que la jointure manque et n'invente aucun QID. Le SQLite ne sert qu'à vérifier l'existence et les libellés de QID, pas à prouver P3916.

L'IA utilise uniquement un modèle Ollama local explicitement indiqué dans le champ « Modèle ». Par défaut, elle est désactivée : il n'existe pas de moteur de génération magique ou gratuit fourni. Les propositions ne sont jamais automatiquement acceptées.

L'UNESCO est diffusée sous **CC BY-SA 3.0 IGO** ; conserver la provenance et vérifier les conditions de réutilisation. Les snapshots logiciels embarqués proviennent des fichiers fournis par l'utilisateur.

## Tests

`python -m unittest discover -s tests -v`
