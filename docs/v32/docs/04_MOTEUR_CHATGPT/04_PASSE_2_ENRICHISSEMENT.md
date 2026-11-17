# Passe 2 — construction intensive de Kristals privés

**V32.1** : l’objet produit par la passe 2 est une **proposition EncyK avec contexte et provenance**, pas un fait déjà admis dans un îlot. Conserver les qualités de volume du moteur ancien; les étapes d’auteur sont dans [admission Kit](../09_FEDERATION_KRISTAL/04_ADMISSION_KIT_REPRISE.md).


## L'orientation voulue

Le deuxième passage est **le cœur du produit**. L'utilisateur privilégie un gigantesque volume de connaissances privées utiles, quitte à faire nettoyer les détails par un agent de finition plus tard. La source Wikipédia complète et le JSON Wikidata original fournissent des matériaux concrets : **leur présence réduit le risque d'hallucination**, sans rendre automatiquement vrais tous leurs énoncés.

## Lecture recommandée

Pour chaque sujet sélectionné :

1. Lire la fiche sujet (QID, concepts UNESCO, routes de sélection et type de sujet).
2. Parcourir l'article Wikipédia **intégral** en suivant une carte de ses sections, sans se limiter à l'introduction ou au guide de lecture. Si plusieurs articles alimentent un sujet, organiser le travail par sources sans dédoubler les faits.
3. Lire les éléments Wikidata structurants disponibles : nature, classes, dates, relations, acteurs, événements et déclarations significatives. Les références originales sont préférées au graphe compact.
4. **Extraire largement** les faits spécifiques, importants et documentés : définitions, mécanismes, contexte, chronologie, relations, causes et conséquences attribuées, décisions, réalisations, œuvres, résultats et contradictions.
5. Rédiger des claims concis et distincts, non de longues paraphrases d'un paragraphe; joindre à chacun un extrait authentique/localisateur de l'article ou une déclaration Wikidata identifiée.
6. Donner un bilan **par sujet/source** des dimensions couvertes et des limites honnêtes. Puis passer au sujet suivant; ne pas repasser trois fois sur le même texte sans raison.

## Quantité sans inflation artificielle

Il n'y a **pas** de nombre maximum ou minimum imposé par article : une petite notice peut soutenir 1–3 faits, un long article historique plusieurs dizaines ou centaines de faits utiles si la matière le justifie. Le prompt doit **chercher systématiquement les dimensions riches**, au lieu de s'arrêter à cinq généralisations après avoir lu le premier écran.

Les doublons, les listes d'étudiants ordinaires, les coordonnées, les chiffres qui vieillissent rapidement, les anecdotes sans importance restent de faible valeur. **La quantité recherchée est le nombre de connaissances utiles distinctes**, pas le nombre de chaînes JSON ou de mots générés. Les faits importants dans des sous-sections tardives comptent autant que les généralités d'introduction.

## Pas de triple vérification

Une extraction, puis **un contrôle local proportionné** de citation/source/identité et de couverture des sections suffisent pour la version de construction. Un deuxième passage ciblé est pertinent lorsqu'un article est vraiment dense ou contient une contradiction importante; ne pas créer trois relectures obligatoires pour chaque article ou chaque fait.

## Travail adapté au contexte disponible

L'outil peut envoyer de gros packs, mais les milliers de pages/centaines de milliers de mots ne tiennent pas automatiquement dans la capacité pratique d'une seule conversation. Le manager calcule des **budgets d'entrée et de sortie** et produit des tâches assez riches, mais réalisables. Si la tâche devient trop grande, la **scinder avant l'envoi** (ou produire un statut de couverture partielle explicite), jamais omettre une grande fraction du lot en prétendant l'avoir couvert.

Le temps humain et le temps du modèle ne sont **pas** des quotas de qualité. Une réponse très rapide avec trois faits pour un article dense est suspecte; une tâche peut être courte lorsqu'elle couvre correctement une petite source. La métrique utile est **la densité des faits sourcés par sujet retenu**, et la couverture des sections principales.

## Distinguer fait et jugement

Un texte Wikipédia peut refléter des opinions, des controverses ou des informations datées : écrire « selon X » ou « l'article rapporte que… » lorsque nécessaire. Ne jamais fabriquer une citation pour atteindre le volume. Les divergences entre Wikipédia et Wikidata sont des **variantes de source**, non un motif pour bloquer toute la branche.

## Deltas et cumul

Chaque claim concerne un `kristal_id` de sujet, non automatiquement l'article source. Plusieurs liens UNESCO/branches peuvent être dérivés de la passe 1. Les répétitions de même fait sont fusionnées; les citations nouvelles peuvent être ajoutées. Le cumul reste privé et évolutif : le nettoyage exhaustif n'est pas la condition de fin du job.
