---
name: plan-governed-implementation
description: Convert approved specification and architecture into ordered, bounded, evidence-driven implementation work packages. Use after the design is stable when a governed change needs dependency order, file ownership, role assignments, test/review evidence, specialist checks, milestones, and rollback-aware execution planning.
---

# Plan Governed Implementation

## Direct invocation boundary

This procedure may modify a governed project only after the orchestrator supplies a validated assignment contract. If invoked directly without that contract, provide only a bounded read-only consultation, return control to `$orchestrate-owner-governed-delivery`, and do not modify a project, accept work, release, or communicate an owner decision. Do not call a direct or sequential pass independent unless a trusted host attests distinct principals; otherwise label it `separate-pass-not-independent`. This behavioral gate does not itself create host-level access control.

Plan vertical slices that remain testable, reviewable, and owner-visible. Do not turn planning into implementation or hide a broad program behind one task.

During active governed delivery, work only under an assignment contract and report to $orchestrate-owner-governed-delivery.

## Procedure

1. Verify approved Foundation, UX Foundation, specification, architecture, risk, artifact fingerprints, and unresolved conditions.
2. Map every approved requirement and quality constraint to one or more work packages and planned proof.
3. Sequence dependencies so compatibility, schema/data preparation, contracts, protected behavior, implementation, testing, review, release readiness, and observation happen in safe order.
4. Define each work package with one objective, exclusions, owned targets, non-overlapping write ownership, inputs, role identities, permission ceiling, acceptance criteria, required tests, review dimensions, specialist checks, rollback impact, and freshness rule.
5. Plan parallel work only when packages have no conflicting files, interfaces, state, data migrations, shared test fixtures, or approval dependencies.
6. Include negative, boundary, permission, concurrency, recovery, UX, security, reliability, migration, documentation, deployment, and observation tasks when applicable.
7. Define owner-visible milestones and their decision packets. Do not ask the owner to approve invisible micro-edits.
8. Write the plan using 'assets/implementation-plan-template.md' and send it to $guard-approved-artifacts.

## Prohibited shortcuts

- Do not assign one agent as implementer, tester, and reviewer.
- Do not call a test or review optional because work is Fast.
- Do not plan work around an unapproved assumption.
- Do not commit to infrastructure, packages, deployment, or data operation without explicit authority.
- Do not collapse independent deliverables solely to reduce paperwork.

## Resources

- 'assets/implementation-plan-template.md' — work-package plan.
- 'references/planning-and-ownership-rules.md' — ownership, dependency, and evidence rules.
