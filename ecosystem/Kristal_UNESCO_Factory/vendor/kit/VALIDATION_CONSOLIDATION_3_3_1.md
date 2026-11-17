# Qualification de consolidation — Kit 3.3.1

**Portée :** mise à jour du Kit seulement ; aucune modification de Manager,
Konstellation, Light, Skope, EncyK ou Arketype n'est prétendue.

- Contrats persistés inchangés : `kristal.discovery/1.0`,
  `kristal.reader-inventory/1.0`, `kristal.reader-profile/1.0`.
- Ajout de `audit-discovery`, diagnostic local, lecture seule et non autorisant,
  pour les futurs adaptateurs consommateurs.
- Ajout de tests de conformité : fraîcheur, legacy, incohérence d'identité,
  disparition ou altération de fichiers, aucune mutation du canon.
- Suppression **du paquet mis à jour** des deux index temporaires du snapshot ;
  utilitaire de nettoyage local contrôlé à la racine.
- Aucun fichier de Kristal ni copie embarquée de `tools/kristal.py` déplacé
  (les exemples doivent rester autonomes).

Commande recommandée : `python scripts/check_repo.py` ; tests ciblés :
`python -m unittest -v tests.test_discovery_interop tests.test_cleanup_gui`.

La réussite des tests locaux ne qualifie pas à elle seule les adaptateurs
Manager/Konstellation/Light, ni les portes C2/C4 ou les accès réseau.
