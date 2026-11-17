# Spek — étude structurelle approfondie : 5 / 127 Kristals

## Ce qui est livré

- Registre provisoire complet des 127 Kristals dans `template_library/wiki/kristal-ai-proposals.json`.
- Cinq revues d'états portables v8, avec indices et SHA-256 des fichiers observés dans `template_library/wiki/kristal-structure-reviews.json`.
- Catalogue HTML `template_library/wiki/CATALOGUE_REVUE_STRUCTURELLE_127.html`.
- Inventaire de 19 besoins en templates spécialisés **non implémentés** dans `specialized-template-designs.json`.
- Mise à jour de l'interface `Spek_Template_Manager.pyw` et comparaison optionnelle d'empreintes à l'ouverture d'un Kristal.
- Exporteur de sources privées (manifeste par défaut) dans `scripts/exporter_sources_pour_analyse_ia.py`.

## Mise à jour du dépôt déjà installé

Fermer Spek. Décompresser le ZIP correctif dans `C:\mycode\Kristal` en acceptant le remplacement des fichiers sous `Spek/`, sans écraser le dossier `.git`.

Relancer `C:\mycode\Kristal\Spek\Spek_Template_Manager.pyw` ou `START_SPEK.bat`.

Dans l'arbre : `Bibliothèque de templates → wiki → Kristals · compositions proposées (127)`.

Sélectionner l'un des cinq Kristals étudiés pour voir sa décomposition et le type de gabarit requis. Pour les 122 autres, la fenêtre indique que l'étude source est encore en attente.

## Limites

Cette livraison **n'implémente pas** les 19 nouveaux layouts et n'a généré ni texte SemantiK ni Wiki. Les cinq revues reposent sur des états portables de l'archive fournie (pas une attestation d'état canonique). Aucune assignation approuvée, aucune publication GitHub, aucune écriture dans `locals`.

## Sources pour étudier les 122 restants

Voir `docs/PROCHAINE_ETAPE_122_KRISTALS.md`. L'exporteur est local, en lecture seule, et n'inclut les données sensibles qu'avec l'option explicite `--include-content`.
