# Backend and Data Checklist

- Enforce authorization and data scope on the server.
- Validate all untrusted input and normalize/serialize safely.
- Define source of truth, transaction boundary, constraints, indexes, and error contract.
- Prevent duplicate, concurrent, and partial operations with idempotency, locking, or reconciliation as needed.
- Keep migrations backward-compatible, rehearsed, observable, recoverable, and reversible where possible.
- Record audit events without leaking secrets or sensitive values.
- Define job retries, timeout, dead-letter/recovery, and result ownership.
- Preserve historical rules and records through versions/effective dates when relevant.
- Require independent QA and review; add security or reliability review on impact.
