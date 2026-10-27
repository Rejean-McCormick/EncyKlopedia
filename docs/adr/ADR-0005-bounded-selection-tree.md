# ADR-0005 — Arbre de sélection borné

Statut : proposé pour v0.2.

Contexte : les filtres plats v0.1 ne représentent pas un pivot conservant la sélection d’origine. Un langage graphe libre ajouterait trop de sémantique et de surface d’exécution au pilote.

Décision : sélection typée, filtres conjonctifs, liens existentiels vers des sous-sélections; profondeur bornée. Les pivots réécrivent cet arbre. L’interface visuelle et les backend adapters partagent le même QuerySpec.

Conséquences : multi-sauts bornés et pivots complets sans variables libres; OR général, cycles, contraintes universelles et qualification arbitraire d’assertions sont différés. Un besoin impossible à exprimer doit être refusé ou conduire à une nouvelle version documentée.

Décisions associées : politique de lecture distincte de Lens; état visuel distinct de requête; lecteur Kristal à qualifier avant projection RDF; SA facultatif.
