# Installation — liaison contrôlée SemantiK → Spek

## Contenu du correctif

- `SPEK_Template_Manager.pyw` (dans le ZIP : `Spek/Spek_Template_Manager.pyw`) : boutons de création de correspondance et d'import de résultats;
- `spek/semantik_transfer.py` : validation stricte de `CommunicationRequest` / `CommunicationResult`, couverture, traçabilité et livraison dans un dossier privé;
- `docs/INTEGRATION_SEMANTIK_2026-11-02_FR.md` : mode d'emploi complet et limites;
- `tests/test_semantik_transfer.py` : tests de transfert et de refus;
- `README.md` : lien documentaire.

## Installation

1. Fermer l'atelier Spek.
2. Conserver une sauvegarde de tes modifications locales et ne pas remplacer `.git`.
3. Extraire le ZIP **depuis le dossier parent de `Spek`** (par exemple `C:\mycode\Spek_Semantic-publishing`). Les chemins du ZIP commencent par `Spek/`.
4. Relancer `Spek_Template_Manager.pyw`.
5. Utiliser les boutons **Préparer la correspondance…** et **Importer des résultats SemantiK…**.

L'import exige que des requêtes et des résultats SemantiK réels existent déjà pour chaque clé de l'article. L'import ne s'autorise ni accès GitHub, ni modification des Kristals, ni élévation du statut linguistique à `qualified`.

Dans le snapshot SemantiK fourni, `konstellation-fr-3` ne passe pas `validate-runtime` : `grammar.pgf` est absent. Ceci n'est pas corrigé par l'installation du patch Spek.
