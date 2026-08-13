# Expand-migrate-contract protocol

Use this order: expand → compatible deployment → bounded backfill → validate → cut over → observe → contract. State dual-read/dual-write only when it is necessary, how conflicts are resolved, and which path remains the source of truth.

For production data, define batch size, pacing, locks/downtime, expected volume, checkpoint, retry/idempotency behavior, permission and tenant scope, backup reference, restore-drill evidence, validation queries, stop thresholds, and whether recovery will roll back or move forward safely. Do not remove old data paths until the agreed observation period ends and recovery evidence remains current.
