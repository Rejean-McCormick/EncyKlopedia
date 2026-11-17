# Construction intensive : deux passes, production provisoire, admission séparée

## Objectif

Préserver le **débit élevé** de la boucle ChatGPT ↔ données locales : dix lanes possibles, gros ZIP autonomes, import partiel réparable, reprise, collecte de faits nombreux et spécifiques. L'IA ne doit pas s'arrêter à une synthèse superficielle; elle doit traiter toute la matière utile reçue. **Un temps de réponse élevé n'est pas un indicateur de qualité à lui seul.** Mesurer couverture de sections, faits utiles distincts, coût, taux de réparation et nouveaux apports.

## Passe 0 — acquisition et candidats indexés (local)

UNESCO 88 branches / P3916 candidats → QID → table locale `wiki_qid` → `page_id` anglais → éventuels voisins P31/P279, SKOS, autres relations pertinentes → fallback lexical. Une route conserve propriété, sens, profondeur, provenance et stratégie. Les pages et extraits sont acquis **une seule fois** quand la révision et le profil sont réutilisables. Ne pas parcourir l'intégralité du XML pour chaque branche.

## Passe 1 — pertinence documentaire

ChatGPT examine **les couples (concept, sujet, article)** ou leur regroupement explicite. Réponses `SELECT`, `REJECT`, `HOLD` argumentées et importables. Sélection généreuse si l'article contient une section réellement pertinente, pas seulement si son titre correspond. Un QID, P3916 ou un voisin de graphe ne déclenche aucune approbation automatique. Les décisions restent provisoires et révisables.

## Passe 2 — enrichissement substantiel des sources retenues

Fournir le texte intégral des articles retenus, à révision déterminée, les déclarations Wikidata pertinentes **avec qualifiers, rangs et références quand disponibles**, le contexte des concepts et les profils de domaine. Réclamer des **propositions typées, nombreuses, non redondantes**, couvrant explications, processus, temporalités, mesures et controverses attribuées, selon la richesse source.

Pour chaque proposition conserver : sujet visé, assertion/contextes, provenance et passage/locator, conditions temporelles, révision source, version du traitement et **îlots cibles possibles**. Les contradictions deviennent variantes contextualisées; ne pas inventer de justification. Éviter la triple validation systématique et les quotas arbitraires de faits.

## Le résultat de la passe 2 N'EST PAS une écriture d'îlot

**Règle de cadence décidée en V32.2 :** poursuivre le cumul de propositions dans EncyK sans attendre la disponibilité d’un auteur Kit. Pour chaque vague mûre, préparer séparément un lot de promotion vers les [Kristals UNESCO existants](09_CUMUL_PRIVE_PROMOTION_DIFFEREE.md); seules ces promotions passent par le Kit, et pas les retours ChatGPT. Les autres branches continuent de produire en parallèle.

Sortie : **registre EncyK de propositions** prêt à la consultation exploratoire et à une admission ultérieure. Ce registre est *pérenne comme historique de travail*, sans devenir un canon encyclopédique indépendant. Un enrichissement ne crée pas automatiquement de workspace ni ne modifie un état Kristal existant.

## Réemploi et idempotence par niveau

| Niveau | Clé indicative | Rejouer quand… |
|---|---|---|
| Acquisition source | `(source, identifiant, révision)` | Révision/source changée |
| Extraction générique | `(source_ref, profil_extraction, version)` | Profil/révision changée |
| Interprétation métier | `(proposition_source, modèle_domaine, version)` | Domaine ou politique change |
| Revue de pertinence | `(candidat, concept, version_contexte)` | Nouvelle preuve/portée |
| Admission dans îlot | `(proposition_id, état_attendu, politique)` et **reçu observé** | État cible ou décision change |

L'« extraction unique et définitive par article » est une fausse optimisation : des domaines différents peuvent interpréter un même texte de manière complémentaire. Dédupliquer la matière brute et les opérations résolues, pas toutes les interprétations du monde.

## Contrôles légers

Identité et article corrects, source/révision observables, citation/passage réellement présent, condition importante préservée, ZIP attendu, retour non rejoué deux fois, items valides importés même si certains sont à réparer. Pas d'exigence de 100 % de Wikipédia, ni d'envoi vers trois modèles réviseurs.
