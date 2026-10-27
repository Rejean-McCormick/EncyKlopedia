# Satellites secondaires et fiches — révision 2 (13 octobre 2026)

## Survol

- Au survol **et au focus clavier** d'un satellite, un anneau secondaire non interactif apparaît en overlay, sans réorienter le centre ni fabriquer des relations.
- L'aperçu est limité à 6 voisins ; son placement tient compte des bulles déjà visibles et des bords du SVG (heuristique déterministe de collisions).
- Le clic sur le satellite garde sa fonction de navigation. L'overlay reste un **aperçu non cliquable** ; il ne remplace pas un deuxième niveau de navigation.
- La requête d'aperçu utilise les politiques de lecture et le même canal API que la constellation. Délai de 140 ms, annulation des requêtes obsolètes, cache borné, invalidé si contexte/lentille/Kristal/authentification changent.

## Fiches

- Badge « i » indépendant sur les personnes, lieux, organisations, œuvres et événements dont **le type est explicitement reconnu**.
- Contenu standardisé par type ; chaque champ vient exclusivement de l'entité. Aucun lieu de naissance, géocodage, date ou image n'est inventé.
- Illustration déclarée : uniquement un chemin raster de même origine (PNG/JPG/WEBP/AVIF/GIF), sans URL externe. Un pictogramme prend le relais si l'image manque ou échoue.
- La fiche est un dialogue **non modal**. Le focus passe au bouton Fermer, puis revient à son badge lorsque la fiche est fermée, y compris via Échap.
- Le composant ne crée pas les assets : intégrer explicitement les illustrations sur le serveur si elles sont déclarées.

## Limites connues

- À forte densité, un placement entièrement sans recouvrement n'est pas garanti (heuristique, non solveur global).
- Le contenu des fiches dépend des métadonnées réellement fournies par `boot.entities`.
- Compilation Astro/Svelte complète et essai navigateur encore requis dans l'environnement local de développement.
- Aucune modification de contrat API, de faits sémantiques, de règles d'accès ou de publication.
