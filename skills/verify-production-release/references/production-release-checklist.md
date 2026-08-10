# Production Release Checklist

## Before authorization

- Verify exact build, technical acceptance, evidence freshness, target, risk, owner authorization, and rollout method.
- Confirm staging/production-like proof, safe configuration, secrets readiness without disclosure, integration readiness, schema/data compatibility, backup/recovery, rollback or forward recovery, capacity, monitoring, alerts, support, and incident authority.
- Define halt, rollback, communication, and reconciliation thresholds.

## During deployment

- Reconfirm the exact authorized target and backup/recovery point.
- Use repeatable deployment mechanisms.
- Record secret-safe output and halt on unexpected migration, health, permission, data, or latency signal.

## After deployment

- Run controlled smoke checks with safe accounts/data.
- Observe health, errors, latency, saturation, jobs, integrations, data quality, critical journey, permissions, and business signal for the approved window.
- Do not call a successful deployment complete until observation and required owner decision are complete.
