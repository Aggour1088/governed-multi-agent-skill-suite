# Performance and Reliability Checklist

- Define measurable objectives before optimizing.
- Record baseline, representative data/traffic, environment, test method, and result.
- Measure critical user, API, database, job, cache, integration, and infrastructure paths affected by the change.
- Verify cache correctness, invalidation, staleness, concurrency, and dependency failure behavior.
- Verify retries, timeouts, idempotency, backpressure, overload, restart, partial failure, and reconciliation.
- Require health checks, logs, metrics, traces, correlation, alerts, dashboards, support ownership, backup/restore, rollback thresholds, and a degradation strategy proportionate to risk.
- Do not run unsafe production load tests or claim production capacity from a local result.
