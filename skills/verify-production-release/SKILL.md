---
name: verify-production-release
description: Gate and verify governed release readiness, deployment authorization, migration and rollback safety, monitoring, production smoke tests, staged rollout, observation, incident response, and closeout. Use before deployment, after deployment, or when deciding whether an exact build is genuinely production-ready.
---

# Verify Production Release

## Direct invocation boundary

This procedure may modify a governed project only after the orchestrator supplies a validated assignment contract. If invoked directly without that contract, provide only a bounded read-only consultation, return control to `$orchestrate-owner-governed-delivery`, and do not modify a project, accept work, release, or communicate an owner decision. Do not call a direct or sequential pass independent unless a trusted host attests distinct principals; otherwise label it `separate-pass-not-independent`. This behavioral gate does not itself create host-level access control.

Treat readiness review, deployment, rollback, and production change as separate actions. Do not deploy, alter production data, or roll back unless the owner explicitly authorizes the exact build, target, method, and window.

During active governed delivery, report release evidence and Go/Conditional Go/No-Go only to $orchestrate-owner-governed-delivery.

## Pre-release gate

1. Verify technical acceptance, owner acceptance where required, exact build/revision, approved target, risk, release authorization state, and evidence freshness.
2. Confirm staging or production-like validation, configuration readiness without exposing secrets, integration readiness, migration compatibility, backup/recovery, rollback/forward recovery, capacity, security, observability, support, and incident ownership.
3. Require a No-Go for Critical or High unresolved defect, failed security/reliability evidence, unsafe migration or rollback, missing recovery point, ambiguous target, unproven permission/data behavior, or missing owner authorization.
4. Return Go, Conditional Go, or No-Go. A conditional decision names condition, owner, containment, deadline, monitoring, and explicit release authority.

## Deployment and observation

When deployment is explicitly authorized:

1. Reconfirm build, target, window, backup, migration, rollback authority, and stop thresholds.
2. Use the existing repeatable deployment process. Do not improvise production edits or bypass protected approval.
3. Record output without secrets and halt on health, migration, integrity, permission, latency, or unexpected-record-count failure.
4. Run controlled production smoke checks with safe accounts and data.
5. Observe agreed health, error, latency, saturation, job, integration, data-quality, and business signals for the proportionate window.
6. Trigger rollback or forward recovery at approved thresholds. Reconcile records and communicate the owner-visible consequence.

Never describe a successful deployment command as feature completion.

## Resources

- 'assets/production-release-record-template.md' — release and observation record.
- 'references/production-release-checklist.md' — readiness, rollout, and recovery checks.
