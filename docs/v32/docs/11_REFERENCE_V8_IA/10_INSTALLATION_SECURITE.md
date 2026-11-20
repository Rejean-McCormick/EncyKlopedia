# 10 — Installation, chemins, diagnostic, protection des données

## Identifier d'abord le dépôt et la distribution

Le ZIP `znapshot_EncyKlopedia_11172030.zip` contient un **snapshot du dépôt V32.2 avec documentation V7** ; il ne contient pas `code_v8/` ni `campagne_v8.py` à son sommet. La **distribution autonome V8** avait été produite séparément. Toujours vérifier sur le poste quel fichier `OUVRIR_ENCYK_V8.cmd` et quel code sont réellement utilisés.

Ne jamais déduire de l'existence de `docs/v32/docs/11_REFERENCE_V8_IA` qu'une V8 a été installée ou même testée : **une documentation n'exécute pas le moteur**.

## Chemins historiques indicatifs (à confirmer sur Windows)

| Ressource | Exemple de chemin | Lecture/écriture prévue |
|---|---|---|
| Dépôt EncyK V32 | `C:\mycode\EncyKlopedia\EncyKlopedia` | Code et docs, seulement modifications autorisées |
| Distribution V8 | `D:\ENCYK_V8` (exemple) | Code autonome, lanceur et station |
| Workspace neuf V8 | `D:\EncyKlopedia\30_working\encyk_v8_NEUF_88` | SQLite EncyK, ZIP, reçus |
| UNESCO vivant | `C:\mycode\EncyKlopedia\UNESCO_Kristals` | Références à lire; canons intouchables |
| Index Wikidata | `D:\EncyKlopedia\30_working\wikidata\wikidata.compact.sqlite` | Lecture seule via Skope/adapter |
| XML et index Wikipédia | `D:\EncyKlopedia\...\wikipedia_en*` | Lecture seule |
| Workspace V32 abandonné | `D:\EncyKlopedia\30_working\encyk_v32_NEUF_87_20261116T202136Z_e2e3c56` | Historique non migré; destruction uniquement si explicitement demandée |

**La suppression du workspace V32 ne fait pas partie de cet overlay**, même si l'utilisateur l'a autorisée lors de l'établissement de V8. Cet overlay ne manipule aucun dossier D:.

## Diagnostic de départ (sans production)

1. Vérifier l'archive et sa version via un reçu de livraison/manifest.
2. Lire le `README.md`, `AGENTS.md` et `docs/v32/docs/11_REFERENCE_V8_IA/00_INDEX.md`.
3. Contrôler la présence des 88 références UNESCO ; distinguer leur copie de la source canonique.
4. Ouvrir le registre **en lecture seule**, vérifier schéma, branches, nombre de candidats/jobs/propositions et absence de migration indésirable.
5. Vérifier les index Skope/Wikipédia en mode RO par un échantillon de requêtes **indexées**, pas un balayage du dump mondial.
6. Vérifier le code de la station V8 si l'objectif est une campagne ; pas de simulation de fonctionnalité à partir d'un document.
7. Avant modification de code, lancer les tests de sa distribution et faire une sauvegarde SQLite cohérente si besoin.

## Protéger les autorités

- Aucun import d'un `ENR` ne doit modifier `C:\...\UNESCO_Kristals\branches\...\canon`.
- Aucun script de l'overlay ne modifie Skope, Kristalizer, la Médiathèque ou les index de 110/134 Go.
- Les archives des prototypes V27–V31 peuvent contenir des bases privées précieuses, mais ne sont pas des sources à importer silencieusement.
- Le nom « Kristal » est surchargé : ne pas créer un îlot par branche ou QID sans contrat autorisé.

## Installer l'overlay documentaire

L'installateur fourni à la racine du pack applique **uniquement des fichiers Markdown de documentation** à un dépôt correspondant au snapshot vérifié. Prévisualisation par défaut, `--apply` explicite, vérification SHA des fichiers connus, sauvegarde avant remplacement, écritures temporaires atomiques et refus en cas de dérive de version. Il ne démarre pas V8, ne produit pas de SEL/ENR et ne purge aucun espace de travail.

Voir `LIRE_EN_PREMIER.md` à la racine de l'overlay et les tests de l'installateur.
