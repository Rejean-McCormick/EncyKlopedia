# Lot 6 — régression V32 après interop fédéré diK V5.9 (24 novembre 2026)

## Frontière et compatibilité

Cette correction est construite **sur le SmartDump EncyKlopedia du 24 novembre 2026, 08:03:49**, après l'overlay DIK_ECOSYSTEM_V5_9_ALIGNEMENT_5_REPOS_PS7. Ses six cibles EncyK (`AGENTS.md`, `README.md`, `docs/v32/docs/13_DIK_INTEROP/00_REGISTRE_FEDERE_V59.md`, `interop/dik-federation-interface-0.1.schema.json`, `tests/test_dik_federation_preflight.py`, `tools/dik_federation_preflight.py`) sont conservées octet pour octet. L'installateur refuse le lot si leurs empreintes locales ne correspondent plus à V5.9.

La fédération diK demeure **candidate, en lecture seule, sans autorité de publication, admission, migration ou écriture canonique**. Aucune source ni dépôt diK n'est modifié par ce lot.

## Corrections limitées

- `tests_v32/test_end_to_end.py` et `tests_v32/test_reliability_v322.py` : fixtures de propriété Wikidata P31 sous la représentation compacte `property_id=31` déjà consommée par `encyk_v32/sources.py` et produite par Skope. Il ne s'agit **pas** d'un identifiant QID Wikidata.
- `encyk_v32/doctor.py` : même propriété P31 dans `EXPLAIN QUERY PLAN`, sans écriture SQL ni changement de schéma.
- `test_lane_limit_and_single_oversize` : budget en **mots souple** pour le premier article et **plafond d'octets strict** ; vérification explicite du blocage `OVERSIZE` lorsque les octets sont réduits à 1.
- `test_portable_example` : contrôle des chemins par les valeurs par défaut et la racine du dépôt, sans exiger une lettre Windows ni exclure artificiellement `/mnt/data` ou `/home/oai`.

## Tests sur copie isolée

```powershell
Set-Location 'C:\mycode\EncyKlopedia\EncyKlopedia'
python -m unittest discover -s tests_v32 -v
python -m pytest -q tests/test_dik_federation_preflight.py
```

Contre-épreuve locale Linux sur le snapshot corrigé : **30/30 tests V32** et **3/3 tests de précontrôle fédéré** réussis. Aucun index massif D:, GUI Windows, publication ou qualification des 5 dépôts V5.9 n'a été testé ici. Conserver les gates privés existants.
