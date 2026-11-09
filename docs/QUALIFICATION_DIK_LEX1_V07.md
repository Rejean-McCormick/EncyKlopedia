# EncyKlopedia → diK — qualification lexicale massive v0.7

**Statut : candidat local. Aucun import normatif diK, aucune publication et aucune identité Kristal créée.**

## Architecture

- **Code et interface** dans le dépôt moteur EncyKlopedia sur **C:**, au même niveau que `package.json`.
- **Données existantes** sous `D:\EncyKlopedia` : **lecture seule** de `index-v1/lexical.sqlite3`, `dik-reconciliation-v1/reconciliation.sqlite3`, `dik-enrichment-v1/enrichment.sqlite3` et des exports probatoires v0.6.
- **Sorties isolées** sous `D:\EncyKlopedia\30_working\lexical\harvester\dik-qualification-v1`.
- Ce module privé ne change ni `src/server.mjs`, ni le lecteur public, ni les dumps, ni le dépôt diK.

## Lancement graphique Windows

Double-cliquer sur `Qualifier_Dictionnaires_diK_UI.pyw` ou `Start_Qualification_diK.cmd` à la racine du moteur **sur C:**. Python 3.10+ et Tkinter requis.

1. **Plan** : vérifier les bases sources, les 6 848 langues et les candidats, sans écrire de données.
2. **Pilote fr/en** : qualifier et contrôler les exports des deux langues ; les checkpoints sont réutilisés dans le monde.
3. **Lancer / reprendre le monde** : classer les candidats des langues restantes avec une transaction par langue. Interruption possible ; relancer la même commande.
4. **Explorer les candidats** : filtrer par langue, préfixe de graphie et catégorie ; afficher des gloses et IDs externes échantillonnés, catégories et chemins des sources.
5. **Annoter** : écrire une note de revue locale avec identifiant du réviseur, justification et disposition non normative. Acceptation interdite.
6. **Licences** : montrer la file des sources originales et ajouter des notes de revue juridique, sans accorder de droit d'usage.
7. **Vérifier SHA-256** : lire les exports v0.7 et comparer aux empreintes manifestées ; vérifier aussi les chaînes des journaux de notes.

CLI facultative (depuis C:) :

```powershell
npm run lexical:dik:qualify:plan
npm run lexical:dik:qualify -- --languages fr,en
npm run lexical:dik:qualify
npm run lexical:dik:qualify:verify
```

## Données produites sur D:

| Fichier | Contenu |
|---|---|
| `qualification.sqlite3` | Une ligne par graphie multiesource candidate, classe, signaux, résumé de provenance, checkpoint par langue et notes locales append-only |
| `review_queue/<code>.jsonl` | Candidats condensés et explicables ; SHA256 par langue, références de preuves et champs limités de v0.6 |
| `source_license_review_queue.csv` | Toutes les sources indexées (210 dans le corpus actuel) ; droits et attribution **inconnus/non approuvés** |
| `languages_qualified.csv` | Nombre de candidats et SHA-256 de chaque export par langue |
| `latest.json` | État consolidé : partiel ou terminé, catégories, frontières de gouvernance |
| `dik-qualification-handoff.candidate.json` | Pointeurs vers la file d'examen, **non conforme à une décision ratifiée diK** |
| `RAPPORT_QUALIFICATION.md` | Rapport lisible, limites et contrôles |

## Catégories de revue (priorité, PAS une décision de fusion)

1. `source_evidence_incomplete` : ancrage source manquant ou famille source non capturée.
2. `possible_lexeme_or_normalization_ambiguity` : plusieurs lexèmes Wikidata ou graphies NFC ramenées à la même clé de recherche.
3. `pos_mapping_review` : différentes étiquettes POS, **sans assimilation automatique** des QID Wikidata aux catégories Kaikki/UniMorph.
4. `sense_comparison_queue` : gloses + identifiants de sens externes disponibles.
5. `limited_sense_evidence` : gloses OU identifiants de sens, preuves limitées.
6. `lemma_morphology_only` : flexions et lemmes sans preuve suffisante des sens.

Plusieurs gloses ne prouvent ni contradiction ni équivalence. Les 23,17 millions de clés uniques v0.4 ne sont **pas** importées ici ; la v0.7 reste centrée sur les ~1,55 million de clés multiesources v0.5, avec **seulement les lignes d'origine échantillonnées** et champs plafonnés par v0.6. Un sens non échantillonné peut manquer.

## Gouvernance et contrats

- `diK/spec/diK-1.0/docs/03_DICTIONNAIRES.md` : LEX-001 à LEX-006. Une graphie n'est pas une clé sémantique, licence obligatoire avant promotion, versionnement et transparence des couches.
- `diK/spec/diK-1.0/docs/04_CONCILIATION.md` : XW-001 à XW-005. Un « candidat unique » n'est pas une identité acceptée ; les rapports doivent exposer signaux et ambiguïtés.
- `diK/spec/diK-1.0/contracts/dik-review-decision.schema.json` : le contrat de décision proposée nécessite une **cible KQ/KP**, un réviseur autorisé et des références `KS` lors d'une acceptation. Le pack v0.7 **ne crée pas** ces références et ne prétend pas produire une décision conforme.
- Les notes locales v0.7 ont pour dispositions `needs_more_evidence`, `defer`, `reject_lexical_candidate`, `escalate_ambiguity`, `escalate_rights`. **Aucun `accepted`**. Elles sont journalisées en ajout seulement, avec chaînage SHA-256 local (pas une notarisation externe).
- Les annotations juridiques v0.7 sont des *signalements* (`needs_legal_review`, `source_license_claim_recorded`, `hold`, `needs_attribution_review`), jamais une approbation de licence. Le fichier de file de licences reste bloqué même après annotation.
- Publication dans EncyKlopedia uniquement après la qualification indépendante C2/C4, licences et identité dans les composants faisant autorité.

## Protection, performance et reprise

Le pack calcule et contrôle le SHA-256 **de chaque export v0.6 lu** ainsi que son nombre de lignes avant d'enregistrer le checkpoint v0.7. Une langue complète ne sera pas retraitée lorsque son entrée et son fichier export semblent inchangés. La vérification complète permet de détecter un fichier v0.7 abîmé même si sa taille est identique. Une langue interrompue est annulée côté SQLite et le fichier temporaire est supprimé. Une coupure après la validation SQLite et avant le remplacement atomique du fichier est récupérable par relancement.

La base de qualification et les exports sont **des objets reconstruisibles dérivés**, jamais la vérité canonique. Conserver plusieurs Go libres sur D:. Le traitement massif sur les données réelles n'est pas simulé par les tests synthétiques. Ni la qualité sémantique ni le nombre exact de décisions acceptées ne peuvent être déduits du seul taux de qualification.

## Étape post-v0.7

Un **adaptateur diK versionné** devra lire uniquement des décisions et licences réellement ratifiées. Il devra créer ou lier les preuves `KS` autorisées, exécuter les validations de schéma du Framework/diK, contrôler l'unicité des alignements exacts, conserver les rejets/supersessions et ne jamais écrire directement dans l'identité Kristal depuis cet outil de collecte.
