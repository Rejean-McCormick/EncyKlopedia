# Réparation du démarrage de Spek — 2 novembre 2026

## Problème confirmé

Message Windows : `No module named 'spek.local_kristals'`.

Le correctif **SPEK_CORRECTIF_PHRASES_SEMANTIK_2026-11-02.zip** incluait `spek/studio_gui.py` mais **pas** `spek/local_kristals.py`, alors que ce dernier est importé par l'interface. Le ZIP complet contenait bien ce module. Le problème apparaît si les correctifs antérieurs n'ont pas été appliqués entièrement.

## Installation

1. Fermer Spek.
2. Sauvegarder tes modifications locales éventuelles dans le dépôt.
3. Extraire `SPEK_CORRECTIF_DEMARRAGE_AUTONOME_2026-11-02.zip` dans **`C:\mycode\Spek_Semantic-publishing`** : il doit créer/remplacer `Spek/spek/local_kristals.py` et `Spek/Spek_Template_Manager.pyw`.
4. Dans `C:\mycode\Spek_Semantic-publishing\Spek`, lancer `VERIFIER_INSTALLATION_SPEK.cmd`.
5. Relancer `START_SPEK.bat`.

Si le diagnostic signale d'autres fichiers absents, installer le **dépôt complet corrigé**, sans écraser `.git`, les sources `locals` ou des données locales personnalisées. Il est préférable de faire une copie de sauvegarde avant d'écraser la bibliothèque du dépôt.

## Garantie de portée

Ce correctif n'analyse aucun Kristal, n'infère aucun template, ne produit aucune phrase de secours et ne publie rien. Il vérifie uniquement la présence de dépendances nécessaires au démarrage. Le diagnostic est une vérification des **fichiers**, pas un contrôle de compatibilité sémantique ni une qualification d'un RuntimeSet.
