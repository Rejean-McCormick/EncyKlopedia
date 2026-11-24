# EncyK ↔ diK V5.9 — frontière du registre fédéré

**Document de raccordement candidat, non admission Framework, non nouvelle branche UNESCO.**

La source canonique des KQ/KP, assertions et preuves reste le Kristal/Framework.
EncyK conserve ses données d'acquisition, son index Wikidata `wiki_qid`, ses
preuves et propositions privées. Le registre fédéré diK est une **vue dérivée**
recherchable par `(namespace_id, KQ/KP)` ou par `Q/P` Wikidata (relations exactes
revues visibles distinctement des candidats). Aucun Wikidata QID ne crée à lui
seul un nouveau Kristal ni une identité locale.

EncyK V32.2 et la distribution autonome V8 sont distincts. Ce correctif vise le
snapshot V32.2 et ne prétend **pas** modifier V8, ses 88 branches ou D:\EncyKlopedia.
Les bases index-v1, reconciliation-v1 et enrichment-v1 sur D: restent en lecture
seule, y compris leurs fichiers WAL. Aucun téléchargement, checkpoint, création
de consensus, fusion de KQ ni promotion d'assertion.

## Contrat d'intégrité proposé

```
python tools/dik_federation_preflight.py --dir C:\mycode\diK\diK\reports\federation-v59-01
```

Le précontrôle lit seulement manifest.json et registry.sqlite3, vérifie le SHA256
et les tables attendues. `INTEGRITY_ONLY` signifie **ni licence ni sens approuvé**.
Le statut source `accepted/exactMatch` de diK n'autorise aucune sélection EncyK.
Les libellés inexistants restent inconnus. Le registre 13 langues n'efface pas
les anciennes données `no` des bases V5.7.

**Évolutions séparées nécessaires :** consultation ciblée de ce registre depuis
le pipeline lexical vivant, qualification du schéma draft.3/draft.4, tests sur
les bases EncyK D:, journal d'acceptation propre à EncyK. Aucune de ces tâches
n'est réalisée par le simple précontrôle.
