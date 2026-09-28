# Interaction Envelope

Normative schema: [`contracts/schemas/envelope.schema.json`](../contracts/schemas/envelope.schema.json).

Core fields include `specversion`, `id`, `class`, `time`, `profile`, `source`, `target`, `subject`, `operation`, `correlation_id`, `causation_id`, `idempotency_key`, `authority`, `data_schema`, `data`, `artifact_refs`, `governance`, `response`, `trace`, `evidence`, and `extensions`.

Durable Command/Query records require a concrete target before durable emission. Correlation, causation and technical trace are distinct.
