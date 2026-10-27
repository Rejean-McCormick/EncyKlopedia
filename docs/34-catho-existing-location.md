# Kristal Catho dans son dossier existant (lecteur local v10)

## Emplacement

Catho n'est **jamais déplacé**. Le lecteur local de Konstellation lit, sans
écrire, ce dossier : `C:\mycode\Kristal\locals\A-Kristal-Catho`.

Le fichier `config/active-reader.json` contient une référence explicite à ce
dossier Windows. Si ton emplacement change plus tard, modifie uniquement
`directory` (JSON avec `/`, par exemple `D:/Kristal/locals/A-Kristal-Catho`).
Ne modifie pas `canon/`, `state/`, `build/v9/` ou le graphe dérivé.

## Lancement

- `Ouvrir_Kristal_Catho_v10.cmd` : vérifie le workspace et ouvre le lecteur
  local v10, puis le navigateur sur `http://127.0.0.1:4321`.
- `Konstellation_Launcher.cmd` : ouvre la configuration active si
  `config/active-reader.json` existe. La variable explicite
  `KONSTELLATION_BACKEND_CONFIG` conserve la priorité.
- `Ouvrir_Theophile_demo.cmd` : charge volontairement l'ancien pack Théophile.

Le lanceur principal affiche `Mode : lecteur Kristal explicitement configure`
et le chemin de `config/active-reader.json` lorsqu'il utilise Catho. Il
n'affiche plus `Pack : ...theophile-biblical.enriched.pack.json` dans ce mode.

Le menu « My Kristals » est activé pour le profil local. Il affiche le lecteur
configuré mais **n'inventorie pas automatiquement tous les dossiers** : une
intégration Manager/export distincte reste requise pour un catalogue complet.
L'ouverture Catho n'est pas une qualification C1, ni une autorisation C2.

## Symptômes courants

- **Théophile encore affiché** : vérifier le nom du lanceur employé, puis le
  journal `Lecteur : ...config\active-reader.json`. Fermer l'ancien serveur
  sur le port 4321 avant de relancer (le lanceur sait gérer une ancienne
  instance Konstellation identifiée).
- **Catho introuvable** : vérifier que `kristal.workspace.json` existe à
  l'emplacement ci-dessus. La version de Catho compatible v10 inclut les
  artefacts dérivés et un Discovery régénéré.
- **Logo 404** : problème d'asset distinct du chargement de corpus.
- **Kompiler 503** : intégration optionnelle non configurée.
- **Fleet 404** : prévisualisation désactivée ou non configurée ; le lecteur
  direct n'en dépend pas.

## Sécurité et limites

Lecteur strictement local (127.0.0.1). L'état sémantique v9 appartient au
modèle Framework v10 ; Konstellation n'écrit pas le canon. Un graphe dérivé
périmé ou aux empreintes contradictoires doit être refusé et régénéré avec
l'Authoring Kit. Les contrats Discovery sont consultatifs et ne sont jamais
des permissions d'accès.

Validation Linux : tests ciblés du lecteur et essai sur les fichiers du ZIP
Catho ; le démarrage du lanceur `.cmd` nécessite un essai séparé sur Windows.
