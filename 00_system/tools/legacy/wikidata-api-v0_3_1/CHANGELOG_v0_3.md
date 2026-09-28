# v0.3

- corrige la décompression HTTP gzip (`UnicodeDecodeError ... 0x8b`);
- ajoute **Estimer taille N1** par échantillon live;
- charge `relations.catalog.csv` dans le `.pyw` après le pull;
- trie les marqueurs par popularité (`people_with_relation`);
- ajoute sélection par cases à cocher;
- ajoute filtre texte / relations sémantiques;
- ajoute profondeur alternée objet/relation;
- ajoute estimation d'expansion avant exécution;
- ajoute expansion récursive des relations sélectionnées vers `output/expansion`;
- conserve la phase N1 sans valeurs et isole explicitement la phase 2 qui suit les valeurs choisies.
