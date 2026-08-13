---
name: specify-approved-change
description: Translate an owner-approved Feature Foundation into unambiguous, testable requirements without changing business intent. Use after final Foundation approval when a governed change needs user stories, rules, contracts, acceptance criteria, exclusions, and clarification records before architecture or planning.
---

# Specify Approved Change

## Direct invocation boundary

This procedure may modify a governed project only after the orchestrator supplies a validated assignment contract. If invoked directly without that contract, provide only a bounded read-only consultation, return control to `$orchestrate-owner-governed-delivery`, and do not modify a project, accept work, release, or communicate an owner decision. Do not call a direct or sequential pass independent unless a trusted host attests distinct principals; otherwise label it `separate-pass-not-independent`. This behavioral gate does not itself create host-level access control.

Turn approved intent into observable requirements. Work only from a Foundation whose approval fingerprint verifies. Treat missing business decisions as blockers, not as technical details to invent.

During active governed delivery, work only under an assignment contract and report to $orchestrate-owner-governed-delivery. When invoked directly, provide a read-only specification consultation and do not modify a project.

## Procedure

1. Verify the Foundation status, approval fingerprint, scope, exclusions, risk, owner decisions, UX Foundation, and unresolved conditions.
2. Map each approved outcome to user-visible behavior, business rule, data effect, role permission, normal path, invalid path, boundary, failure, recovery, and acceptance evidence.
3. Define terms, source of truth, invariants, calculation examples, effective dates, historical behavior, idempotency expectations, notification, audit, and integration contracts when applicable.
4. Separate functional requirements, quality requirements, operational constraints, acceptance criteria, exclusions, and deferred decisions.
5. Define success in observable terms. Avoid framework, service, schema, or component choices unless an approved constraint truly requires them.
6. Capture clarification only when it does not alter the approved outcome. Return scope, user, rule, permission, workflow, owner-control, or material UX changes to the Foundation gate.
7. Build traceability from each requirement to acceptance criteria and planned evidence.
8. Copy 'assets/specification-template.md' to the feature governance location and identify its input fingerprint.

## Quality bar

Require a different agent to be able to implement and test the specification without guessing a business rule. Reject ambiguous verbs such as 'support', 'handle', or 'fast' unless their observable conditions are defined.

Do not treat a test list as a specification or a technical plan as a business decision.

## Handoff

Hand the specification to $architect-system-deliberately and $plan-governed-implementation. Require $guard-approved-artifacts before implementation.

## V2 contract and evidence boundary

Route this work through `$using-governed-suite` and the current v2 contract. Classify material statements as **Verified**, **Reproducible**, **Reported**, **Inferred**, **Unknown**, or **Failed**. Only an allowed E2+ host or CI receipt may support **Verified**; an unapproved requirement remains **Reported** or **Unknown**. Stop if the Foundation, business rule, acceptance evidence, scope, or freshness is missing or stale.

## Resources

- 'assets/specification-template.md' — specification artifact.
- 'references/specification-quality-checklist.md' — ambiguity and traceability checks.
