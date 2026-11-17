# Architecture des dossiers

```text
workspace/
├── mediatheque/
│   ├── 05_TOOLS/
│   ├── 06_GUI/
│   ├── schemas/sqlite/
│   ├── contracts/
│   ├── docs/
│   └── tests/
└── content/
    ├── 01_DB/
    ├── 02_STORAGE/
    ├── 03_IMPORTS/
    ├── 04_EXPORTS/
    ├── 07_BACKUPS/
    ├── 08_LOGS/
    ├── kristals/
    ├── documents/
    └── config.toml
```

`mediatheque/` est versionnable et ne contient pas de données privées. `content/` est l'état local et doit rester privé.
