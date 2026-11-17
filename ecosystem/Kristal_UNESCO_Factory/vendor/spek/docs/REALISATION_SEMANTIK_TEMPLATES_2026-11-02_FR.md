# Spek — Phrases SemantiK dans les templates

## Distinction fondamentale

Spek ne **rédige pas** à partir des triplets d'un Kristal. La liste de relations canoniques est du matériau d'audit, pas du texte destiné au Wiki. Le plan privé affiche désormais « Texte en attente de réalisation SemantiK », sans faire apparaître les triplets en lecture courante.

Le rendu **éditorial** utilise un `article.json` avec des sections, des layouts et des unités explicitement sélectionnés. **SemantiK Architect** réalise les phrases de chaque unité à partir de requêtes sémantiques explicites. Spek contrôle les obligations, les références aux sources, l'identité déterministe et la langue de chaque résultat, puis les place dans les slots définis par les layouts.

Le registre des **127 propositions IA** n'est ni un ensemble de requêtes, ni une sélection autorisée d'assertions, ni une preuve de qualification linguistique. Pour les cinq Kristals étudiés, les positions des assertions constituent une **revue structurelle**, non une autorisation de publication.

## Dans l'interface

1. Sélectionner un Kristal et consulter son plan documentaire.
2. Préparer `article.json` avec les slots correspondant aux templates prescrits et les faits expressément retenus pour cette rédaction. Spek ne sélectionne pas les faits à la place de l'éditeur.
3. Préparer les **CommunicationRequest** de SemantiK Architect et le fichier `mapping.json` en associant chaque clé de réalisation à **une requête**.
4. Dans **Aperçu Wiki**, cliquer **Réaliser avec SemantiK…** et choisir :
   - `article.json`;
   - `mapping.json` contenant les chemins `requests/*.json`;
   - le dépôt `SemantiK-Architect` installé localement;
   - au besoin, le répertoire des RuntimeSets GF/PGF et le snapshot canonique associé.
5. Spek appelle le CLI **officiel** SemantiK Architect en sous-processus. Si toutes les requêtes réussissent, Spek passe les résultats au vérificateur `semantik_transfer`, puis propose **Prévisualiser le Wiki**.

Un `mapping.json` préparatoire peut être créé avec **Préparer une correspondance…**. Il ne fabrique pas les requêtes sémantiques : celles-ci doivent être concrètes et traçables.

## Commande locale équivalente

```powershell
cd C:\mycode\Spek_Semantic-publishing\Spek
py -3 -m spek.semantik_execution `
  --article C:\chemin\article.json `
  --mapping C:\chemin\mapping.json `
  --architect C:\mycode\Kristal\SemantiK-Architect `
  --runtime-root C:\mycode\Kristal\SemantiK-Architect\runtime
```

La commande écrit une **nouvelle sortie temporaire privée**, sans modifier `locals`, `article.json`, les requêtes ou le RuntimeSet. Le chemin de `realizations.json` vérifié est affiché à la fin.

## Contrôle bloquant

Une réalisation est refusée si le RuntimeSet ne peut pas rendre, si une clé de template n'a pas de requête, si une obligation n'est pas couverte, si des références source manquent, si les langues divergent ou si l'identité déterministe ne correspond pas.

Le snapshot `SemantiK Architect 11021338` n'est pas prêt à réaliser le français sur le profil `konstellation-fr-3` tel que livré : `grammar.pgf` manque dans le dossier de ce RuntimeSet. Spek ne fournit **aucune phrase artificielle en remplacement**. Installer et qualifier un RuntimeSet complet dans SemantiK est nécessaire avant la génération linguistique réelle.

Ni la réussite de SemantiK, ni celle de la compilation Spek ne valent approbation de publication : C1/C2/C3 restent indépendants, et aucun push GitHub n'est déclenché.
