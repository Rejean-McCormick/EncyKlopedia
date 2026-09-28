# Frontière entre corpus et IA

## Architecture conceptuelle

```text
sources
  ↓
curation / extraction / validation
  ↓
CORPUS CANONIQUE
  ↓
retrieval / filtres / règles
  ↓
interface conversationnelle facultative
```

## Ce qui est non génératif

Le corpus canonique :

- ne produit pas une nouvelle assertion à chaque requête ;
- contient des unités précompilées ;
- peut être haché et versionné ;
- peut être interrogé sans LLM.

## Ce qui reste génératif

Un chatbot peut :

- choisir une mauvaise assertion ;
- résumer maladroitement ;
- introduire une phrase non supportée ;
- confondre une nuance.

Il doit donc être traité comme une **interface faillible**.

## Règles du chatbot

1. Répondre à partir du corpus récupéré.
2. Afficher les sources et les statuts.
3. Ne pas inventer de statut doctrinal absent.
4. Dire « le corpus ne contient pas assez d'éléments » lorsque nécessaire.
5. Permettre d'ouvrir les assertions sous-jacentes.
6. Garder la réponse du modèle distincte de l'artefact canonique.

## Avantage institutionnel

Changer de modèle ne détruit pas la mémoire structurée.

Le Saint-Siège pourrait utiliser :

- un modèle commercial ;
- un modèle local ;
- un moteur de recherche déterministe ;
- une interface documentaire sans IA ;
- plusieurs interfaces simultanément.
