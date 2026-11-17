# V32.1 — décision d'architecture : EncyK fédéré, production rapide

**Statut : [CIBLE] · révision documentaire du 16 novembre 2026.** Cette page prévaut, sur les points contradictoires, sur les propositions V32 datées du 15 novembre. Elle **n'affirme pas** que les adaptateurs ou les contrats du Kristal Framework sont déjà implémentés dans EncyK.

## Décision courte

**Précision V32.2 :** la production courante accumule dans EncyK, puis une phase distincte de [promotion différée](09_CUMUL_PRIVE_PROMOTION_DIFFEREE.md) pousse des lots mûrs vers les îlots Kristal propriétaires, y compris les espaces UNESCO préparés **si leur contrat d’auteur est qualifié**. Aucune intégration Kristal par retour ZIP.

Un **produit EncyK**, un **manager `.pyw` racine**, plusieurs **états Kristal sous leurs autorités respectives**, et un **registre EncyK pour produire, sélectionner, tracer et proposer**. La lecture est fédérée; l'écriture dans un îlot n'intervient que via un auteur supporté et qualifié. EncyK ne crée pas un canon encyclopédique rival.

Skope et Kristalizer demeurent externes et intouchés. Les 88 branches UNESCO structurent la navigation et le tri des candidats; elles ne dictent pas le découpage physique des îlots. La branche `unesco.mt1.10` peut être laissée en archive comme production historique, sans imposer sa migration aux 87 autres branches.

## Ce qui change par rapport à V32.0

| Ancienne simplification | Arbitrage V32.1 | Impact concret |
|---|---|---|
| « Un QID = un Kristal » | QID = identifiant possible d'un **sujet**, pas création automatique d'un **îlot** | On peut traiter 1 000 QID sans créer 1 000 workspaces |
| `subject_kristal`/`fact_claim` V32 propriétaires de la connaissance | EncyK conserve **propositions, tâches et projections**; états admis dans les Kristals propriétaires | Les nouvelles tables EncyK ne sont pas un deuxième canon |
| Enrichir = écrire directement les claims dans le Kristal | Enrichir = **produire des propositions sourcées**. Admission distincte, ultérieure ou par politique bornée | Forte cadence sans tout bloquer sur un chemin d'auteur |
| Migrer/archiver tous les îlots pour unifier | **Fédérer et lire d'abord**; migrations sélectives seulement après nécessité démontrée | Préserve les îlots réels, y compris anciens |
| UNESCO = partition des Kristals | Relations **N:N** sujet–concept–branche–îlot | Un îlot peut couvrir plusieurs sujets et branches |
| Un « vrai pourcentage de fin » nécessaire | Campagnes avec rendement, gaps, coûts et statut explicite; **pas de complétude absolue** | Accepte la finition ultérieure par agents |
| Règles universelles pour toutes les données | Profils par domaine avec conservation des conditions, qualifications et contradictions | Education ≠ Soil ≠ Accounting |

## Limites de provenance de cette décision

Le [rapport d'architecture reçu le 16 novembre](../08_REFERENCES/07_RAPPORT_DECISION_20261116.md) mentionne Kristal Framework, Authoring Kit, Integration Pack, Arketype, Manager, Kompiler, KristalDiag, LOT-K50 et Kristal-Wikidata-Workflow. **Ces dépôts ne figurent pas tous dans le SmartDump EncyK disponible pour cette révision**. Ses conclusions sur leurs tests, références et capacités sont donc des **constats rapportés**, à corroborer sur ces dépôts avant intégration réelle; ne pas prétendre les avoir retestées ici.

## Obligations minimales réellement utiles

- Identités stables et source révisable; passage et conditions associés aux propositions importantes.
- Retour ZIP idempotent; aucune copie silencieuse d'un fait admis; état exact pour admission/reprise.
- Ne pas inventer de citations, ni assimiler une correspondance candidate à une identité exacte.
- Pas de triple revue par défaut, pas de SHA de dump entier à chaque batch, pas de migrations obligatoires avant la première lecture.
- Publication externe séparée de la collecte locale et de l'admission dans un espace privé.

## Direction d'exécution

**A** lire/fédérer les îlots existants → **B** collecter et produire des propositions par deux passes → **C** démontrer une admission supportée sur Education puis Soil → **D** fédérer les snapshots et compiler un contexte fidèle → **E** augmenter le débit à partir des mesures. Voir [plan de réalisation](07_LOTS_A_E.md).
