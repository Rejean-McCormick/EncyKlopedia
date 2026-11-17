# __TITLE__

**Type :** Local Kristal  
**Workspace :** `kristal.local-workspace/3.2.0`  
**État :** `kristal.state/9.0`

## Travail local

```bash
python tools/kristal.py check .
python tools/kristal.py build-v9 .
```

Le build v9 n'active aucune couche IA par défaut.

## IA / Kompiler (optionnel)

```bash
python tools/kristal.py build-ai .
python tools/kristal.py check-ai .
python tools/kristal.py pack-ai . --output __TITLE__-portable-ai.zip
```

## Synchronisation GitHub et publication

- **Kristal Manager** : validation + synchronisation de la surface de lecture sous `kristals/<slug>/` dans une collection GitHub publique ou privée.
- **Kristal GitHub Setup / Bootstrap** : qualification, publication et activation réseau.

La synchronisation de lecture et la publication sont indépendantes de l'identité sémantique du state.
