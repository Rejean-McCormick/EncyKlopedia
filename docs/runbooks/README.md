# Runbooks Konstellation

- [Startup / readiness](STARTUP.md)
- [Rollback](ROLLBACK.md)
- [Backup / restore](BACKUP-RESTORE.md)
- [Threat model](THREAT-MODEL.md)
- [Incident](INCIDENT.md)
- [Upgrade](UPGRADE.md)

Ces runbooks complètent [OPERATIONS.md](../OPERATIONS.md). Toute instance partagée/publique doit adapter les commandes à son orchestrateur, son reverse proxy, son stockage canonique et sa gestion de secrets. Les projections et caches Konstellation sont reconstructibles et ne remplacent jamais le Kristal canonique dans un plan de reprise.
