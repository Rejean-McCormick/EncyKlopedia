# Métadonnées de provenance

## Objectif

Permettre à un ingénieur ou archiviste de comprendre exactement :

- qui a préparé l'édition ;
- quand ;
- avec quelle version de schéma ;
- quels outils ont construit et validé l'artefact ;
- quelles licences s'appliquent ;
- quelles sources externes sont référencées.

## Recommandation de fichiers

```text
PROVENANCE.md
VERSION
manifest.sha256.json
licenses/
  framework.txt
  corpus.txt
  third-party-notes.md
```

## PROVENANCE.md — contenu minimal

- Présenté par : Théophile
- Contact : theophile.systems@gmail.com
- Site : https://www.theophile.systems/
- Date d'édition
- Identifiant de version
- Version du format sémantique
- Description du pipeline de build
- Description du pipeline de validation
- Limites connues
- Historique de migration du format si pertinent

## Règle

La provenance ne doit être ni une bannière marketing ni un easter egg.

C'est une propriété normale de l'artefact.
