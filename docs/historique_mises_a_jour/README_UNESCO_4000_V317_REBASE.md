# v31.7 — UNESCO 4 000 — rebase compatible avec le préchargement v31.6.1

Cet overlay est basé sur les fichiers EXACTS fournis dans `ENCYK_SOURCES_ACTUELLES_V317.zip` et conserve les améliorations natives du presse-papiers et du préchargement automatique déjà présentes dans le Python et le JavaScript locaux.

Portée : constantes de dimensionnement UNESCO (`REVIEW_SIZE=4000`, `MIN_REVIEW_SIZE=3000`, `MAX_REVIEW_SIZE=4000`, `REVIEW_BUDGET=16000`), consignes des nouvelles revues, télémétrie, libellé UI. Kristal 120 articles / 400 000 mots demeure inchangé. UNESCO n'est pas redécouvert ni réinitialisé par l'installation. Les tâches et preuves précédentes demeurent intactes.

Réserves : le ZIP de revue à 4 000 candidats et ses contextes peut être volumineux; vérifier la qualité des premiers retours, notamment les APPROVE/REJECT/HOLD. Le ZIP de code ne traite aucune tâche en cours.

Procédure : fermer la station, la relancer avec LANCER_ENCYKLOPEDIA.cmd, prévalider le ZIP dans « Mises à jour logicielles » et confirmer si les empreintes correspondent. Redémarrer après installation. Aucun contournement des préconditions.
