# Konstellation — amélioration du langage naturel (FR)

**Base** : `znapshot_Konstellation_10171209.zip` (snapshot fourni le 17 octobre 2026)

## Modifications

- Libellés français explicitement connus pour propriétés Wikidata et prédicats de la projection Catho, notamment `P138 → Nommé d’après`, `academicien_sur_liste_publiee → Source attestant une inscription sur une liste d’académiciens`.
- Pour les codes Wikidata inconnus, repli explicite `Propriété Wikidata P… (libellé indisponible)` : le logiciel **n’invente aucun sens**.
- Astrolabe : recherche aux limites de mots, ce qui empêche `aquin` de se faire passer pour une correspondance de `Joaquín`; répartition de notices de noms identiques sans fusionner leur identité; indication claire des résultats affichés.
- Facettes : les options sans valeur et les types de nœuds purement techniques sont masqués sauf si un filtre est déjà actif.
- Détails : `not_evaluated`, `unspecified`, `read_only_local_projection` affichés en français. Les identifiants sources sont conservés sous les détails techniques.
- Constellation : les métadonnées `v9:node_kind` ne monopolisent plus les groupes de relations proposés.
- Titres d’hypothèses (`wikidata_identity · …`) explicités comme **propositions non vérifiées**.

## Données et autorité

Aucun changement du canon Catho, aucun ajustement aux données de Kristal Manager, Interaction Kernel ou Daat. Les relations originales, leurs identifiants, leurs sources et leurs statuts sont préservés. Les deux fichiers `config/local-catalog.json` et `config/active-reader.json` ne sont pas modifiés, afin de préserver les chemins configurés chez l’utilisateur.

## Contrôles exécutés

| Contrôle | Résultat |
|---|---|
| Tests Node du lecteur v10 et du langage naturel | 15/15 réussis |
| `node scripts/check-svelte-structure.mjs` | 19 fichiers ; 0 problème |
| `node scripts/check-frontend-security.mjs` | 24 fichiers ; 0 problème |
| `node scripts/check-docs.mjs` | 75 documents, 81 liens ; 0 problème |
| Projection réelle Catho | 4 527 entités, 13 217 assertions, 50 définitions de relations |
| P138 sur Catho | 2 arêtes correctement intitulées « Nommé d’après » |

**Limite :** Astro/Svelte n’a pas été compilé et testé intégralement ici : les dépendances Node du snapshot ne sont pas installées dans le runtime de vérification et aucun test graphique Windows n’a été effectué. Les tests statiques Svelte ne remplacent pas `npm run build` ni des tests de navigateur. Aucune prétention de conformité universelle à tous les prédicats ou de traduction automatique des œuvres en langue étrangère.

## Installer

1. Arrêter Konstellation et sauvegarder `C:\mycode\Konstellation\Konstellation`.
2. Extraire le ZIP correctif **dans ce dossier**, en gardant la hiérarchie des chemins et en remplaçant les fichiers correspondants.
3. Démarrer `Konstellation.cmd` et sélectionner Catho dans « Mes Kristals ».
4. Tester la recherche `aquin`, la fiche « Albert le Grand », les facettes, la constellation et les relations `P138`.
5. En cas d’erreur de build, restaurer la sauvegarde et partager le journal exact.
