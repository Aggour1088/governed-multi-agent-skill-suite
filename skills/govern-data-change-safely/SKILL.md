---
name: govern-data-change-safely
description: Govern schema migrations, production data backfills, imports, exports, corrections, retention changes, and data recovery through a bounded expand-migrate-contract plan. Use whenever a governed work package can alter persistent data, database schema, tenant scope, records, backups, or recovery behavior.
---

# Govern Data Change Safely

Treat data changes as a lifecycle, not a single migration command. Prefer reversible expansion, bounded idempotent backfill, validation, observation, and delayed contraction.

## Direct invocation boundary

This procedure may inspect a data-change proposal directly, but it must not modify a project, schema, records, backup, production environment, or release state unless `$orchestrate-owner-governed-delivery` provides an active Enhanced or Critical assignment contract. If invoked without that contract, provide only a bounded read-only consultation and do not modify a project. Do not provide a “safe migration” completion claim from a plan or self-written log alone.

## Procedure

1. Validate the active work-package contract and classify data, tenancy, environment, user impact, change class, data volume, lock/downtime risk, and irreversibility.
2. Create a plan from `assets/data-change-plan.template.json` and validate it with `scripts/validate_data_change_plan.py` before execution.
3. Expand first: add a backward-compatible schema or interface. State old/new application compatibility and the source of truth.
4. Backfill only in bounded, resumable, idempotent batches with progress, error, pause, retry, and cancellation records. Never use production exports as casual test data.
5. Validate counts, hashes, samples, business invariants, authorization, and tenant boundaries. Bind results to the exact revision and data window.
6. Cut over only after compatible deployment order and evidence. Observe declared errors, latency, data drift, and business signals.
7. Contract old paths only after the observation window, recovery check, and fresh approval remain valid.
8. Record backup/restore point, rollback or forward-recovery decision, and exact stop thresholds. A backup without a tested restore is not Verified evidence.

## Evidence and authority labels

Use the v2 labels from `$using-governed-suite`. A plan is **Reported** or **Reproducible**. It becomes stronger only with a host or CI receipt that binds the exact migration, revision, environment, and validation result. Production data requires Enhanced or Critical scope and E2+ declared evidence minimum; this skill cannot create host attestation by itself.

## Resources

- `assets/data-change-plan.template.json` — expand-migrate-contract plan.
- `assets/data-change-receipt-template.md` — evidence and observation record.
- `references/expand-migrate-contract-protocol.md` — compatibility and recovery rules.
- `scripts/validate_data_change_plan.py` — plan validator.
