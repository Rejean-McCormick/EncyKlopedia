# Spek ↔ SemantiK Architect — transfert local explicite

**État : adaptateur de transfert privé implémenté. Pas de production de requêtes, de qualification linguistique ou de publication automatique.**

Ce raccordement s'appuie sur les contrats vérifiés dans les snapshots fournis le 2 novembre 2026 :

- **SemantiK Architect `1.3.0-alpha.2`** : `CommunicationRequest/1.0` → `CommunicationResult/1.0` via la commande `render` et un RuntimeSet effectivement admis.
- **SemantiK Runtime Orchestrator `1.2.0`** : gestion **distincte** des releases GF/PGF, conformance, transactions et activation. **Ce n'est pas un moteur de génération de phrases.**
- **Spek** : `kristal.layout-article-source/0.1` + `kristal.layout-realizations/0.1` → assemblage HTML/PDF/LaTeX, puis brouillon privé Wiki selon le pipeline/gates existants.

## Ce qui est possible dès maintenant

Dans `Spek_Template_Manager.pyw` :

1. **Ouvrir un Kristal** pour voir les compositions proposées (cela ne génère pas de requête SemantiK).
2. Préparer l'article `article.json` à partir d'une sélection éditoriale explicite des structures, sections et unités. Le registre de 127 propositions **n'est pas** une sélection d'assertions prête à publier.
3. Cliquer sur **Préparer la correspondance…**, choisir `article.json`, la langue (`fr`, `en` ou `it`) et un nouveau `semantik-mapping.json`.
4. Pour **chaque clé de réalisation** de l'article, l'éditeur/projection amont doit fournir une requête `CommunicationRequest` avec `request_id`, obligations, graphe et références de sources explicites. Ne pas construire ces requêtes automatiquement à partir du nom du Kristal.
5. SemantiK Architect doit réaliser chaque requête avec **un RuntimeSet réellement disponible** et écrire un `CommunicationResult` JSON distinct, dans le chemin `results/…` indiqué par le mapping. Le mapping conserve la correspondance clé → requête → résultat; modifier les chemins si nécessaire.
6. Cliquer sur **Importer des résultats SemantiK…** et choisir l'article et le mapping. Spek vérifie toutes les clés utilisées, la langue/locale, les obligations, la couverture, les sources, le profil, l'identité déterministe et les contrats de layouts.
7. Après import, **Vérifier** puis **Prévisualiser en HTML**. Le rendu est **local, privé, non qualifié et non publié**.

L'outil ne se connecte pas à un service réseau et ne récupère rien à partir du Kristal au moment de l'import. Il refuse toute clé manquante, toute référence hors du dossier de transfert, tout résultat altéré et tout dossier de sortie déjà existant.

## Exemple de mapping

La génération de correspondance produit un document de cette forme, contenant autant de lignes que de clés effectivement utilisées dans l'article :

```json
{
  "format": "spek.semantik-transfer/1.0",
  "language": "fr",
  "note": "CHEMINS A COMPLETER : aucune requête ni réalisation produite par Spek.",
  "bindings": {
    "title": {
      "request": "requests/title-cd2a...json",
      "result": "results/title-cd2a...json"
    }
  }
}
```

Ce fragment est **illustratif**, et non un mapping directement exécutable; la fonction **Préparer la correspondance…** produit les vrais noms déterministes.

## Utilisation de la ligne de commande Spek

```powershell
cd C:\mycode\Spek_Semantic-publishing\Spek
py -3 -m spek.semantik_transfer --article C:\chemin\article.json --mapping C:\chemin\semantik-mapping.json --out C:\chemin-prive\transfert-001
```

Le dossier `--out` ne doit **pas** exister et doit être **hors des dépôts Git** et hors des dossiers contenant les fichiers source. Ajouter `--state-snapshot C:\chemin\state-snapshot.json` si `article.json` possède `source.origin = kristal_v9` (validation de référence source Spek, pas preuve cryptographique JCS).

La sortie comporte `realizations.json` et `transfer-report.json`, avec les empreintes SHA-256 des fichiers utilisés. Le statut est **`PRIVATE_IMPORTED_NOT_QUALIFIED`**, même si le résultat SemantiK déclare un RuntimeSet : le transfert ne fait aucune authentification de sa release.

## Invocation réelle de SemantiK Architect

Le snapshot fournit une interface CLI explicite :

```text
python -m semantik_architect.adapters.inbound.cli.main --runtime-root <chemin-runtime> render <CommunicationRequest.json>
```

Il faut installer correctement le dépôt Architect et ses dépendances, notamment une grammaire GF/PGF conforme, **avant** toute réalisation. L'interface Spek actuelle ne lance pas cette CLI : elle **importe des résultats préalablement produits** et évite ainsi de feindre une disponibilité du runtime.

Pour examiner l'état réel du RuntimeSet :

```text
python -m semantik_architect.adapters.inbound.cli.main --runtime-root <chemin-runtime> validate-runtime <runtime_set_id>
```

**Contrôle des snapshots fournis :** `validate-runtime konstellation-fr-3` répond `valid: false`, car `runtime/konstellation-fr-3/grammar.pgf` est absent. Le fichier d'activation et les déclarations `RELEASED` ne suffisent pas à démontrer qu'une réalisation est disponible. Les profils MathKristal/Informath restent candidats dans ce snapshot.

## Autorisations et responsabilités

| Étape | Autorité |
|---|---|
| Choisir les templates et les sections | IA, hors exécution Spek, puis revue éditoriale |
| Choisir les assertions et états canoniques exacts | Éditeur/projection amont et contrôles d'identité |
| Planifier et réaliser les phrases | SemantiK Architect + runtime GF/PGF qualifié |
| Libérer/activer les RuntimeSets | SemantiK Runtime Orchestrator |
| Valider et assembler les contenus fournis | Spek |
| C1/C2/C3 et publication Wiki GitHub | Pipeline externe Kristal-Manager / dépôt public |

**Aucune de ces étapes n'est automatiquement promue en « approuvée » par l'import.** Une vraie publication exige le contrôle externe du RuntimeSet, de la source, des contenus éditoriaux et des gates. Spek ne pousse aucun fichier vers GitHub.

## Limites de provenance

La fonction vérifie l'intégrité **interne** d'un `CommunicationResult` (dont son `deterministic_result_id`) et sa compatibilité avec la requête donnée. Ces vérifications ne constituent **ni une signature cryptographique, ni une preuve indépendante que cette requête précise a généré le résultat**, car le résultat SemantiK n'embarque pas directement un hash de sa requête. Le rapport conserve donc les deux empreintes et le lien explicite fourni par l'opérateur. La qualification finale et la preuve d'authenticité restent des contrôles externes.
