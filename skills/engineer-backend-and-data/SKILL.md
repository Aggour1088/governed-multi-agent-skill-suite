---
name: engineer-backend-and-data
description: Implement or inspect governed backend, API, database, authorization, transaction, migration, job, audit, retention, and recovery behavior. Use only for bounded server-side or data-layer work assigned by the owner-governed orchestrator.
---

# Engineer Backend and Data

## Direct invocation boundary

This procedure may modify a governed project only after the orchestrator supplies a validated assignment contract. If invoked directly without that contract, provide only a bounded read-only consultation, return control to `$orchestrate-owner-governed-delivery`, and do not modify a project, accept work, release, or communicate an owner decision. Do not call a direct or sequential pass independent unless a trusted host attests distinct principals; otherwise label it `separate-pass-not-independent`. This behavioral gate does not itself create host-level access control.

Implement server-side behavior that remains correct under invalid input, permissions, concurrency, interruption, retry, and recovery. Make the server the enforcement boundary; client behavior is never enough.

During active governed delivery, accept only a bounded assignment contract from $orchestrate-owner-governed-delivery. Do not test, review, accept, release, or report directly to the owner for the same package.

## Procedure

1. Verify approved inputs, scope, data classification, owned targets, architecture, contract, baseline, and permission ceiling.
2. Inspect existing domain model, schema, migrations, conventions, authorization path, transactions, jobs, audit logging, retention, and operational constraints.
3. Define or preserve API contracts, validation, authorization, tenant/organization isolation, source of truth, error behavior, idempotency, concurrency, rate limits, and audit events.
4. Use database constraints, transactions, locking, indexes, migrations, compatibility, backfill/reconciliation, and rollback plans proportionately to the change.
5. Handle timeouts, retries, duplicate delivery, partial failure, dead-letter or recovery behavior, and observable errors where applicable.
6. Keep owner-controlled policy separate from secrets, infrastructure, and protected technical configuration.
7. Use $develop-test-first for behavioral change unless the assignment documents a proportionate exception.
8. Return self-check evidence, exact implementation fingerprint, migration/rollback implication, and limitations. Request independent QA, review, security, or reliability checks as required.

## Stop and escalate

Stop for an unapproved data operation, unknown data ownership, missing authorization model, unsafe migration, unverified schema compatibility, financial/calculation ambiguity, sensitive-data exposure, new dependency, or architecture change.

## V2 contract and evidence boundary

Route this work through `$using-governed-suite` and the current v2 contract. Classify material statements as **Verified**, **Reproducible**, **Reported**, **Inferred**, **Unknown**, or **Failed**. Only an allowed E2+ host or CI receipt may support **Verified**; self-written logs remain **Reported** or **Reproducible**. Stop if the data contract, authorization, migration recovery, or evidence freshness is missing or stale.

## Resources

- 'assets/backend-data-change-record-template.md' — implementation return record.
- 'references/backend-and-data-checklist.md' — server and data correctness checks.
