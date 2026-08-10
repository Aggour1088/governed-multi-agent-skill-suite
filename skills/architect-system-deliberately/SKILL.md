---
name: architect-system-deliberately
description: Inspect an actual software system and produce evidence-based, proportional architecture decisions for an approved change. Use when a governed feature affects boundaries, data ownership, APIs, integrations, migrations, compatibility, scale, recovery, security, or technical trade-offs.
---

# Architect System Deliberately

## Direct invocation boundary

This procedure may modify a governed project only after the orchestrator supplies a validated assignment contract. If invoked directly without that contract, provide only a bounded read-only consultation, return control to `$orchestrate-owner-governed-delivery`, and do not modify a project, accept work, release, or communicate an owner decision. Do not call a direct or sequential pass independent unless a trusted host attests distinct principals; otherwise label it `separate-pass-not-independent`. This behavioral gate does not itself create host-level access control.

Choose the smallest architecture that preserves approved outcomes under real constraints. Inspect before proposing. Treat a design preference, fashionable pattern, or imagined scale as insufficient evidence.

During active governed delivery, work only under an assignment contract and report to $orchestrate-owner-governed-delivery. Do not implement, self-approve, or make business decisions.

## Procedure

1. Inspect the real repository, runtime topology, module boundaries, schema, migrations, interfaces, tests, deployment path, operating constraints, and prior decisions.
2. State verified constraints, unknowns, compatibility obligations, failure modes, data ownership, trust boundaries, and risk assumptions.
3. Compare viable options against approved requirements, existing conventions, delivery cost, operational burden, reversibility, migration safety, isolation, performance, recovery, and future change cost.
4. Define boundaries, ownership, interfaces, state transitions, source of truth, validation, authorization, audit trail, idempotency, concurrency, retries, timeouts, degradation, backup/restore, and rollback behavior as applicable.
5. Avoid premature microservices, generic abstraction, unmeasured caches, new dependencies, queues, databases, or infrastructure components. Justify every addition.
6. Write an architecture record and ADRs with alternatives, decision, rationale, consequences, risks, validation, and reversal path.
7. Escalate a change that affects business scope, UX, cost, legal requirement, or owner-approved outcome.

## Architecture decision test

A decision is incomplete when it lacks: current-state evidence, options, trade-offs, compatibility, failure and recovery behavior, data/permission ownership, observability, and a verification strategy proportionate to risk.

## Handoff

Hand the architecture record to $plan-governed-implementation. Request $secure-and-protect-system or $engineer-performance-and-reliability when the impact matrix requires their input.

## Resources

- 'assets/architecture-record-template.md' — architecture and ADR structure.
- 'references/architecture-decision-checklist.md' — proportional decision checks.
