# Orgo reference adapter

The Orgo adapter is intentionally thin. It reuses `IntegrationOperation`, `OutboxMessage` and `OutboxWorker` rather than creating IK-specific persistence.
