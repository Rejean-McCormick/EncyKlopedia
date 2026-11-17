# Overlay additif UNESCO GF — Audit des preuves v2

**Dépôt cible** : `C:\mycode\Kristal\Kristal_UNESCO_Factory`

Décompresser ce ZIP directement à la racine de ce dépôt. Cet overlay **ajoute uniquement** :

- `tools/unesco_gf_pilot/audit_archive.py`
- `tools/unesco_gf_pilot/tests/test_audit_archive.py`
- ce document

Il ne remplace aucun fichier existant. Aucun déploiement, changement de RuntimeSet ou exécution GF n'est effectuée par cet audit : il ne fait que vérifier la cohérence de pièces archivées. L'audit s'exécute avec la bibliothèque standard Python 3.10+.

## Audit d'un ZIP de résultat

```powershell
cd C:\mycode\Kristal\Kristal_UNESCO_Factory
py -3.12 tools\unesco_gf_pilot\audit_archive.py 'C:\Users\rejea\Downloads\Kristal_UNESCO_Pilote_20261103-181714-863512.zip' --json "$HOME\Downloads\UNESCO_concept10_audit.json"
```

Ne pas traiter le statut `EVIDENCE_CONSISTENT_CANDIDATE_NOT_RELEASED` comme une validation éditoriale ou une autorisation de publication. La compilation a eu lieu sur la machine d'origine selon les logs; l'audit ne relance pas le moteur et ne prouve pas la qualité linguistique.

## Tests automatiques

```powershell
py -3.12 -m unittest discover -s tools\unesco_gf_pilot\tests -p 'test_audit_archive.py' -v
```

## Après le pilote

- Le GF du pilote ne fait que concaténer `String` + `String` + `String`. Passage à la **RGL/grammaires typées** nécessaire pour une réalisation linguistique robuste.
- Le contenu actuel possède deux phrases par concept (présence et rattachement au microthésaurus), pas d'article encyclopédique riche.
- Le transfert Spek utilise l'étiquette interne `status: fixture`. Cela ne signifie pas que GF a été simulé, mais **ne doit pas** être lu comme une qualification éditoriale.
- Validation de références, de définitions, revue humaine et gates de release restent à faire avant tout déploiement.
