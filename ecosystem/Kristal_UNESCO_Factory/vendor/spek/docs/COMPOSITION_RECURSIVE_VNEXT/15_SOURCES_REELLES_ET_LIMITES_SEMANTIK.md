# 15 — Références réelles, réalisations SemantiK et critères de complétude

**État : test d'ancrage réel réussi, réalisation linguistique réelle non démontrée.**

## Contrôle réalisé sur Kristal-Agriculture

Le 3 novembre 2026, le test local en lecture seule a examiné le graphe `.kristal/v11/semantic-graph.json` inclus dans l'archive des cinq Kristals précédemment fournie. Ce graphe contient **391 assertions**. Une instance de template `rhetorical.assertion@1.0.0` a été liée **explicitement** à l'identifiant d'une assertion existante. Le contrôle `compose-source-check` a confirmé **1 champ / 1 référence présente**, sans divulguer l'identifiant, la source ou le hash dans son message.

Ce contrôle **ne prouve pas** :

- que la source v11 est le dernier état canonique approuvé de ton poste ;
- que deux assertions peuvent être reliées par cause, preuve, analogie ou concession ;
- que l'assertion sélectionnée convient à une page publique ;
- qu'une formulation française GF/PGF existe ou est qualifiée ;
- qu'une sortie Spek est autorisée par C1/C2/C3.

La source canonique n'est pas incluse dans cette livraison Spek. L'instance de contrôle a été conservée hors du dépôt distribué pour ne pas publier d'identifiant interne par accident.

## Commande de contrôle pour un utilisateur disposant de sa propre instance

```powershell
py -3 -m spek compose-source-check `
  --instance "C:\CheminPrive\composition.instance.json" `
  --state-source "C:\mycode\Kristal\locals\Kristal-Agriculture\.kristal\v11\semantic-graph.json"
```

Chaque feuille à vérifier peut déclarer `source_assertion_refs` dans son `text_slot`. L'outil vérifie **l'existence des identifiants seulement**, pas la relation, la vérité ni le bon état épinglé. Le contrôleur exige un fichier local JSON v11 explicite et n'analyse pas `locals` pour inventer des correspondances.

## Ce que les snapshots SemantiK permettent de confirmer

Les sources de **SemantiK Architect** et de **SemantiK Runtime Orchestrator** sont disponibles. Les archives examinées ne contiennent pas de fichier `.pgf` compilé. Les contrôles de forme et l'import vérifié `CommunicationRequest` → `CommunicationResult` restent accessibles, mais **nous n'avons pas obtenu de véritables phrases GF/PGF à partir du graphe Agriculture dans cette livraison**.

En attendant un RuntimeSet qualifié, les exemples du dépôt utilisent des **fixtures fictives écrites manuellement**, avec un statut de test explicite. Aucun résultat manuel ne doit être présenté comme produit par SemantiK.

## Chemin encore nécessaire pour la première page réelle

1. Le processus éditorial approuve le choix d'assertions et les relations rhétoriques qui les unissent.
2. Chaque champ de Spek reçoit une `CommunicationRequest` provenant de ces assertions, sans supposer les relations non établies.
3. Un RuntimeSet SemantiK qualifié réalise chaque petite phrase, y compris les éventuelles transitions.
4. Spek valide la couverture et l'identité de chaque résultat, puis assemble les pages à l'aide des modèles discursifs.
5. Le Manager valide la sélection, le rendu et le lot C1/C2/C3, puis la publication Wiki est une opération distincte.

**Définition pratique de « complet » :** un vrai Kristal généré avec des formulations réelles qualifiées, un document fluide, des liens de source exacts en interne, aucune donnée interne dans les pages lecteur et aucune publication sans autorisation.
