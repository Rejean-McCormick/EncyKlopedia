# Validation Skope 0.13.12 — zone secondaire

- Zone prioritaire (Q16 Canada) et zone secondaire (Q49 Amérique du Nord) visibles et éditables sous le Kristal dans l’interface principale.
- Mode annoter (conseillé), strict sur signaux documentés, ou désactivé.
- Aucune modification avant un clic sur Appliquer les zones.
- Synchronisation bidirectionnelle avec le Wizard ; les modifications géographiques invalident les vieux compteurs.
- Le backend existant `geography.py` accepte déjà les deux QID et les exporte dans le scope. Aucun scan du dump ni accès supplémentaire à D:.
- La géographie reste une annotation basée sur liens agrégés, non une preuve de présence.
