# Note technique courte

## Artefact

Le corpus est un état sémantique structuré accompagné de :

- sources et localisateurs ;
- index ;
- documentation ;
- scripts de build ;
- validateur ;
- outil de requête locale ;
- manifestes d'empreintes.

## Propriétés importantes

### Inspectabilité

Chaque assertion peut être examinée indépendamment d'une réponse de chatbot.

### Reproductibilité

Le build est conçu pour reconstruire un état identique à partir de l'entrée éditoriale lorsque les mêmes entrées et outils sont utilisés.

### Intégrité

Les identifiants et empreintes permettent de détecter des modifications de contenu.

### Portabilité

Le cœur du système est textuel et peut être conservé ou interrogé hors ligne.

### Découplage du modèle

Le corpus ne dépend pas d'un LLM particulier. Une interface IA est remplaçable.

## Ce que les validations ne signifient pas

Un PASS technique ne signifie pas :

- imprimatur ;
- reconnaissance du Saint-Siège ;
- vérité métaphysique d'une proposition ;
- absence possible de toute erreur éditoriale.

Il signifie que l'artefact respecte les contrôles techniques annoncés.
