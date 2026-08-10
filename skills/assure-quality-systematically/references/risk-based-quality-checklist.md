# Risk-Based Quality Checklist

## Always test

- Approved acceptance criteria.
- Normal behavior and one meaningful invalid or boundary path.
- Relevant regression behavior.
- Exact implementation fingerprint and raw output.
- Separate tester identity from implementer and reviewer.

## Add when relevant

- Role permission and data isolation.
- Calculation golden cases and historical rules.
- Duplicate submission, concurrency, retry, interruption, timeout, and recovery.
- API/integration contracts and compatibility.
- Migration, backfill, reconciliation, rollback, and data quality.
- UI/UX audit, accessibility, localization, responsiveness, realistic volume.
- Performance, security, privacy, and operational failure behavior.

## Evidence discipline

A screenshot proves only what is visible. A build proves only compilation. A successful test run without the required scenario does not prove the scenario. Record unavailable evidence as unavailable.
