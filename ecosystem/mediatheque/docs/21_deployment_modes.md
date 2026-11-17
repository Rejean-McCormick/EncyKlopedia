# Engine et instances

Médiathèque possède un **Engine unique** et un nombre quelconque d’instances.

```text
mediatheque/                  -> Engine, code uniquement
mediatheque-privee/           -> données/config locale privée
mediatheque-uckk/             -> configuration UCKK
mediatheque-universite-math/  -> configuration Université Math
```

Une différence de contenu, de site ou de fonds ne crée pas un nouvel Engine. Chaque instance choisit son backend et ses paramètres dans `mediatheque.instance.toml`.

Pour les instances filesystem/SQLite, le dossier d’instance est passé à l’Engine comme `KOA_CONTENT_ROOT`. Pour les instances Moodle, le manifeste sélectionne l’adapter Moodle partagé de l’Engine.
